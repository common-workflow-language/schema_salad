use std::{fmt, marker::PhantomData};

use salad_types::SaladType;
use serde::de::{self, DeserializeSeed};

use super::{IntoDeserializeSeed, SeedData};

/// A list helper deserializer, which allows flexible deserialization of data
/// represented either as maps or sequences of objects.
///
/// Particularly useful when dealing with configurations or data formats
/// that might represent the same logical structure in different ways.
/// For example, in YAML:
///
/// ```yaml
/// # Format 1: Sequence of maps with explicit keys
/// entries:
///   - key1: value1
///     key2: value2
///
/// # Format 2: Nested map structure with the first value acting as a key
/// entries:
///   value1:
///     key2: value2
///
/// # Format 3: Map structure with key-predicate pairs
/// # Where:
/// #   - The map key becomes the value for the specified `key` field
/// #   - The map value becomes the value for the specified `predicate` field
/// entries:
///   value1: value2
/// ```
pub struct MapToListSeed<'sd, T> {
    key: &'static str,
    data: &'sd SeedData,
    pred: Option<&'static str>,
    _phant: PhantomData<T>,
}

impl<'de, 'sd, T> MapToListSeed<'sd, T>
where
    T: SaladType + IntoDeserializeSeed<'de, 'sd>,
{
    /// Creates a new [`MapDeserializeSeed`] with the specified key and seed data.
    ///
    /// # Arguments
    ///
    /// * `key` - The field name that will be used as the key in the deserialized structure
    /// * `data` - Additional seed data needed for deserialization
    ///
    /// # Examples
    ///
    /// ```no_run
    /// # use serde::de;
    /// # use crate::de::{MapDeserializeSeed, SeedData};
    /// # let data = SeedData;
    /// // For mapping without a predicate
    /// let seed = MapDeserializeSeed::new("class", &data);
    /// ```
    pub fn new(key: &'static str, data: &'sd SeedData) -> Self {
        Self {
            key,
            data,
            pred: None,
            _phant: PhantomData,
        }
    }

    /// Creates a new [`MapDeserializeSeed`] with the specified key, predicate, and seed data.
    ///
    /// # Arguments
    ///
    /// * `key` - The field name that will be used as the key in the deserialized structure
    /// * `pred` - Predicate field name that enables the simpler key-value mapping format
    /// * `data` - Additional seed data needed for deserialization
    ///
    /// # Examples
    ///
    /// ```no_run
    /// # use serde::de;
    /// # use crate::de::{MapDeserializeSeed, SeedData};
    /// # let data = SeedData;
    /// // For mapping with a predicate
    /// let seed = MapDeserializeSeed::with_predicate("class", "key", &data);
    /// ```
    pub fn with_predicate(key: &'static str, pred: &'static str, data: &'sd SeedData) -> Self {
        Self {
            key,
            data,
            pred: Some(pred),
            _phant: PhantomData,
        }
    }
}

impl<'de, 'sd, T> de::DeserializeSeed<'de> for MapToListSeed<'sd, T>
where
    T: SaladType + IntoDeserializeSeed<'de, 'sd>,
{
    type Value = Box<[T]>;

    fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
    where
        D: de::Deserializer<'de>,
    {
        struct MapVisitor<'sd, T> {
            key: &'static str,
            pred: Option<&'static str>,
            data: &'sd SeedData,
            _phant: PhantomData<T>,
        }

        impl<'de, 'sd, T> de::Visitor<'de> for MapVisitor<'sd, T>
        where
            T: SaladType + IntoDeserializeSeed<'de, 'sd>,
        {
            type Value = Box<[T]>;

            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("a map or sequence of objects")
            }

            fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
            where
                A: de::MapAccess<'de>,
            {
                use serde::__private::de::{Content, ContentDeserializer};

                let capacity = map.size_hint().unwrap_or(1);
                let mut entries = Vec::with_capacity(capacity);

                while let Some((key, value)) = map.next_entry::<Content<'de>, Content<'de>>()? {
                    let value_map = match (value, self.pred) {
                        (Content::Map(mut value_map), _) => {
                            // Format 2: Add the key field to the existing map
                            let key_field = Content::Str(self.key);
                            value_map.reserve_exact(1);
                            value_map.push((key_field, key));
                            value_map
                        }
                        (value, Some(pred)) => {
                            // Format 3: Build a map from key-value pair
                            let key_field = Content::Str(self.key);
                            let predicate_field = Content::Str(pred);
                            vec![(key_field, key), (predicate_field, value)]
                        }
                        (_, None) => {
                            return Err(de::Error::custom(format!(
                                "field `{}` requires a map or predicate value",
                                self.key
                            )));
                        }
                    };

                    // Deserialize the created map into the target type
                    let deserializer = ContentDeserializer::new(Content::Map(value_map));
                    let entry = T::deserialize_seed(self.data).deserialize(deserializer)?;
                    entries.push(entry);
                }

                Ok(entries.into_boxed_slice())
            }

            fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
            where
                A: de::SeqAccess<'de>,
            {
                // Format 1: Sequence of objects
                let capacity = seq.size_hint().unwrap_or(0);
                let mut entries = Vec::with_capacity(capacity);

                while let Some(entry) = seq.next_element_seed(T::deserialize_seed(self.data))? {
                    entries.push(entry);
                }

                Ok(entries.into_boxed_slice())
            }
        }

        deserializer.deserialize_any(MapVisitor {
            key: self.key,
            pred: self.pred,
            data: self.data,
            _phant: PhantomData,
        })
    }
}

#[cfg(test)]
mod tests {
    use salad_types::{SaladAny, SaladObject};
    use serde::__private::de::{Content, ContentDeserializer};

    use super::*;

    fn setup_test_deserializer<'s>(
        input: &'s str,
    ) -> ContentDeserializer<'s, serde_yaml_ng::Error> {
        let content: Content<'s> = serde_yaml_ng::from_str::<Content>(input).unwrap();
        ContentDeserializer::new(content)
    }

    #[test]
    fn list_entries() {
        let input = r#"
            - class: class_1
              key: value_1
            - class: class_2
              key: value_2
            - class: class_3
              key: value_3
        "#;

        let deserializer = setup_test_deserializer(input);
        let to_match = SaladAny::String("value_2".into());
        let object_list = de::DeserializeSeed::deserialize(
            MapToListSeed::<'_, SaladObject>::new("class", &SeedData),
            deserializer,
        );

        assert!(object_list.is_ok_and(|r| matches!(r[1].get("key"), Some(s) if s == &to_match)))
    }

    #[test]
    fn map_entries() {
        let input = r#"
            class_1:
                key: value_1
            class_2:
                key: value_2
            class_3:
                key: value_3
        "#;

        let deserializer = setup_test_deserializer(input);
        let to_match = SaladAny::String("value_2".into());
        let object_list = de::DeserializeSeed::deserialize(
            MapToListSeed::<'_, SaladObject>::new("class", &SeedData),
            deserializer,
        );

        assert!(object_list.is_ok_and(|r| matches!(r[1].get("key"), Some(s) if s == &to_match)))
    }

    #[test]
    fn map_entries_with_predicate() {
        let input = r#"
            class_1: value_1
            class_2: value_2
            class_3:
                key: value_3
        "#;

        let deserializer = setup_test_deserializer(input);
        let to_match = SaladAny::String("value_2".into());
        let object_list = de::DeserializeSeed::deserialize(
            MapToListSeed::<'_, SaladObject>::with_predicate("class", "key", &SeedData),
            deserializer,
        );

        assert!(object_list.is_ok_and(|r| matches!(r[1].get("key"), Some(s) if s == &to_match)))
    }
}
