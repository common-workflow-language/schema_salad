use std::{fmt, marker::PhantomData};

use salad_types::SaladType;
use serde::de;

use super::{IntoDeserializeSeed, SeedData};

/// A list helper deserializer for handling both a single value or a list of values
/// of type `T`.
///
/// This is useful for configurations where a field might accept either a single value
/// or a list of values with the same semantics.
pub struct SingleOrManySeed<'sd, T> {
    pub(super) data: &'sd SeedData,
    pub(super) _phant: PhantomData<T>,
}

impl<'de, 'sd, T> de::DeserializeSeed<'de> for SingleOrManySeed<'sd, T>
where
    T: SaladType + IntoDeserializeSeed<'de, 'sd>,
{
    type Value = Box<[T]>;

    fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
    where
        D: de::Deserializer<'de>,
    {
        struct SingleOrManySeedVisitor<'sd, T> {
            data: &'sd SeedData,
            _phant: PhantomData<T>,
        }

        impl<'de, 'sd, T> SingleOrManySeedVisitor<'sd, T>
        where
            T: SaladType + IntoDeserializeSeed<'de, 'sd>,
        {
            // Private helper method to reduce duplication
            #[inline]
            fn visit_single_value<V, E>(&self, value: V) -> Result<Box<[T]>, E>
            where
                E: de::Error,
                V: de::IntoDeserializer<'de, E>,
            {
                let deserializer = de::IntoDeserializer::into_deserializer(value);
                de::DeserializeSeed::deserialize(T::deserialize_seed(self.data), deserializer)
                    .map(|t| Box::from([t]))
            }
        }

        impl<'de, 'sd, T> de::Visitor<'de> for SingleOrManySeedVisitor<'sd, T>
        where
            T: SaladType + IntoDeserializeSeed<'de, 'sd>,
        {
            type Value = Box<[T]>;

            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("one or a list of values")
            }

            fn visit_bool<E>(self, v: bool) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_single_value(v)
            }

            fn visit_i8<E>(self, v: i8) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_i32(v as i32)
            }

            fn visit_i16<E>(self, v: i16) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_i32(v as i32)
            }

            fn visit_i32<E>(self, v: i32) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_single_value(v)
            }

            fn visit_i64<E>(self, v: i64) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_single_value(v)
            }

            fn visit_u8<E>(self, v: u8) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_i32(v as i32)
            }

            fn visit_u16<E>(self, v: u16) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_i32(v as i32)
            }

            fn visit_u64<E>(self, v: u64) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_single_value(v)
            }

            fn visit_f32<E>(self, v: f32) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_single_value(v)
            }

            fn visit_f64<E>(self, v: f64) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_single_value(v)
            }

            fn visit_str<E>(self, v: &str) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_single_value(v)
            }

            fn visit_string<E>(self, v: String) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_single_value(v)
            }

            fn visit_bytes<E>(self, v: &[u8]) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_single_value(v)
            }

            fn visit_byte_buf<E>(self, v: Vec<u8>) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                self.visit_single_value(v)
            }

            fn visit_map<A>(self, map: A) -> Result<Self::Value, A::Error>
            where
                A: de::MapAccess<'de>,
            {
                let deserializer = de::value::MapAccessDeserializer::new(map);
                de::DeserializeSeed::deserialize(T::deserialize_seed(self.data), deserializer)
                    .map(|t| Box::from([t]))
            }

            fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
            where
                A: de::SeqAccess<'de>,
            {
                let capacity = seq.size_hint().unwrap_or(8);
                let mut entries = Vec::with_capacity(capacity);

                while let Some(entry) = seq.next_element_seed(T::deserialize_seed(self.data))? {
                    entries.push(entry);
                }

                Ok(entries.into_boxed_slice())
            }
        }

        deserializer.deserialize_any(SingleOrManySeedVisitor {
            data: self.data,
            _phant: PhantomData,
        })
    }
}

#[cfg(test)]
mod tests {
    use salad_types::SaladAny;
    use serde::__private::de::{Content, ContentDeserializer};

    use super::*;

    #[test]
    fn single_object_entry() {
        let input = r#"
            type: object
            key: value
        "#;

        let deserializer: ContentDeserializer<'_, serde_yaml_ng::Error> = {
            let content: Content<'static> = serde_yaml_ng::from_str::<Content>(input).unwrap();
            ContentDeserializer::new(content)
        };

        let object = de::DeserializeSeed::deserialize(
            <Box<[SaladAny]>>::deserialize_seed(&SeedData),
            deserializer,
        );

        assert!(object.is_ok_and(|r| matches!(r[0], SaladAny::Object(_))))
    }

    #[test]
    fn single_primitive_entry() {
        let input = r#"Hello, World!"#;

        let deserializer: ContentDeserializer<'_, serde_yaml_ng::Error> = {
            let content: Content<'static> = serde_yaml_ng::from_str::<Content>(input).unwrap();
            ContentDeserializer::new(content)
        };

        let string = de::DeserializeSeed::deserialize(
            <Box<[SaladAny]>>::deserialize_seed(&SeedData),
            deserializer,
        );

        assert!(string.is_ok_and(|r| matches!(r[0], SaladAny::String(_))))
    }

    #[test]
    fn multiple_entries() {
        let input = r#"
            - 1
            - 2.0
            - true
            - Hello, World!
            - type: object
              key: value
        "#;

        let deserializer: ContentDeserializer<'_, serde_yaml_ng::Error> = {
            let content: Content<'static> = serde_yaml_ng::from_str::<Content>(input).unwrap();
            ContentDeserializer::new(content)
        };

        let string = de::DeserializeSeed::deserialize(
            <Box<[SaladAny]>>::deserialize_seed(&SeedData),
            deserializer,
        );

        assert!(string.is_ok_and(
            |r| matches!(r[1], SaladAny::Float(_)) && matches!(r[3], SaladAny::String(_))
        ))
    }
}
