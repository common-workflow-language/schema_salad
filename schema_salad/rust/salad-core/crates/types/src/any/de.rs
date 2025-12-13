use std::{collections::hash_map, slice};

use compact_str::CompactString;
use serde::de;

use super::{SaladAny, SaladObject};

/// Deserializer for converting SaladAny values into SaladTypes
pub(super) struct SaladAnyDeserializer<'de>(pub &'de SaladAny);

impl<'de> de::Deserializer<'de> for SaladAnyDeserializer<'de> {
    type Error = de::value::Error;

    fn deserialize_any<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        match self.0 {
            SaladAny::Bool(b) => visitor.visit_bool(*b),
            SaladAny::Int(i) => visitor.visit_i32(*i),
            SaladAny::Long(l) => {
                if super::INT_RANGE.contains(l) {
                    visitor.visit_i32(*l as i32)
                } else {
                    visitor.visit_i64(*l)
                }
            }
            SaladAny::Float(f) => visitor.visit_f32(*f),
            SaladAny::Double(d) => {
                if super::FLOAT_RANGE.contains(d) {
                    visitor.visit_f32(*d as f32)
                } else {
                    visitor.visit_f64(*d)
                }
            }
            SaladAny::String(s) => visitor.visit_str(s),
            SaladAny::Object(o) => visitor.visit_map(SaladObjectMapAccess::new(o)),
            SaladAny::List(l) => visitor.visit_seq(SaladAnyListSeqAccess::new(l)),
        }
    }

    fn deserialize_bool<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        static ERR_MSG: &str = "boolean";

        match self.0 {
            SaladAny::Bool(b) => visitor.visit_bool(*b),
            SaladAny::Int(1) | SaladAny::Long(1) => visitor.visit_bool(true),
            SaladAny::Int(0) | SaladAny::Long(0) => visitor.visit_bool(false),

            // Errors
            SaladAny::Int(i) => Err(de::Error::invalid_type(
                de::Unexpected::Signed(*i as i64),
                &ERR_MSG,
            )),
            SaladAny::Long(l) => Err(de::Error::invalid_type(de::Unexpected::Signed(*l), &ERR_MSG)),
            SaladAny::Float(f) => Err(de::Error::invalid_type(
                de::Unexpected::Float(*f as f64),
                &ERR_MSG,
            )),
            SaladAny::Double(d) => Err(de::Error::invalid_type(de::Unexpected::Float(*d), &ERR_MSG)),
            SaladAny::String(s) => Err(de::Error::invalid_type(de::Unexpected::Str(s), &ERR_MSG)),
            SaladAny::Object(_) => Err(de::Error::invalid_type(de::Unexpected::Map, &ERR_MSG)),
            SaladAny::List(_) => Err(de::Error::invalid_type(de::Unexpected::Seq, &ERR_MSG)),
        }
    }

    fn deserialize_i32<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        static ERR_MSG: &str = "signed integer";

        match self.0 {
            SaladAny::Int(i) => visitor.visit_i32(*i),
            SaladAny::Long(l) if super::INT_RANGE.contains(l) => visitor.visit_i32(*l as i32),

            // Errors
            SaladAny::Bool(b) => Err(de::Error::invalid_type(de::Unexpected::Bool(*b), &ERR_MSG)),
            SaladAny::Long(l) => Err(de::Error::invalid_type(de::Unexpected::Signed(*l), &ERR_MSG)),
            SaladAny::Float(f) => Err(de::Error::invalid_type(
                de::Unexpected::Float(*f as f64),
                &ERR_MSG,
            )),
            SaladAny::Double(d) => Err(de::Error::invalid_type(de::Unexpected::Float(*d), &ERR_MSG)),
            SaladAny::String(s) => Err(de::Error::invalid_type(de::Unexpected::Str(s), &ERR_MSG)),
            SaladAny::Object(_) => Err(de::Error::invalid_type(de::Unexpected::Map, &ERR_MSG)),
            SaladAny::List(_) => Err(de::Error::invalid_type(de::Unexpected::Seq, &ERR_MSG)),
        }
    }

    fn deserialize_i64<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        static ERR_MSG: &str = "signed long integer";

        match self.0 {
            SaladAny::Long(l) => visitor.visit_i64(*l),
            SaladAny::Int(i) => visitor.visit_i64(*i as i64),

            // Errors
            SaladAny::Bool(b) => Err(de::Error::invalid_type(de::Unexpected::Bool(*b), &ERR_MSG)),
            SaladAny::Float(f) => Err(de::Error::invalid_type(
                de::Unexpected::Float(*f as f64),
                &ERR_MSG,
            )),
            SaladAny::Double(d) => Err(de::Error::invalid_type(de::Unexpected::Float(*d), &ERR_MSG)),
            SaladAny::String(s) => Err(de::Error::invalid_type(de::Unexpected::Str(s), &ERR_MSG)),
            SaladAny::Object(_) => Err(de::Error::invalid_type(de::Unexpected::Map, &ERR_MSG)),
            SaladAny::List(_) => Err(de::Error::invalid_type(de::Unexpected::Seq, &ERR_MSG)),
        }
    }

    fn deserialize_f32<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        static ERR_MSG: &str = "float";

        match self.0 {
            SaladAny::Float(f) => visitor.visit_f32(*f),
            SaladAny::Double(d) if super::FLOAT_RANGE.contains(d) => visitor.visit_f32(*d as f32),

            // Errors
            SaladAny::Bool(b) => Err(de::Error::invalid_type(de::Unexpected::Bool(*b), &ERR_MSG)),
            SaladAny::Int(i) => Err(de::Error::invalid_type(
                de::Unexpected::Signed(*i as i64),
                &ERR_MSG,
            )),
            SaladAny::Long(l) => Err(de::Error::invalid_type(de::Unexpected::Signed(*l), &ERR_MSG)),
            SaladAny::Double(d) => Err(de::Error::invalid_type(de::Unexpected::Float(*d), &ERR_MSG)),
            SaladAny::String(s) => Err(de::Error::invalid_type(de::Unexpected::Str(s), &ERR_MSG)),
            SaladAny::Object(_) => Err(de::Error::invalid_type(de::Unexpected::Map, &ERR_MSG)),
            SaladAny::List(_) => Err(de::Error::invalid_type(de::Unexpected::Seq, &ERR_MSG)),
        }
    }

    fn deserialize_f64<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        static ERR_MSG: &str = "double";

        match self.0 {
            SaladAny::Double(d) => visitor.visit_f64(*d),
            SaladAny::Float(f) => visitor.visit_f64(*f as f64),

            // Errors
            SaladAny::Bool(b) => Err(de::Error::invalid_type(de::Unexpected::Bool(*b), &ERR_MSG)),
            SaladAny::Int(i) => Err(de::Error::invalid_type(
                de::Unexpected::Signed(*i as i64),
                &ERR_MSG,
            )),
            SaladAny::Long(l) => Err(de::Error::invalid_type(de::Unexpected::Signed(*l), &ERR_MSG)),
            SaladAny::String(s) => Err(de::Error::invalid_type(de::Unexpected::Str(s), &ERR_MSG)),
            SaladAny::Object(_) => Err(de::Error::invalid_type(de::Unexpected::Map, &ERR_MSG)),
            SaladAny::List(_) => Err(de::Error::invalid_type(de::Unexpected::Seq, &ERR_MSG)),
        }
    }

    fn deserialize_str<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        static ERR_MSG: &str = "UTF-8 string";

        match self.0 {
            SaladAny::String(s) => visitor.visit_str(s),

            // Errors
            SaladAny::Bool(b) => Err(de::Error::invalid_type(de::Unexpected::Bool(*b), &ERR_MSG)),
            SaladAny::Int(i) => Err(de::Error::invalid_type(
                de::Unexpected::Signed(*i as i64),
                &ERR_MSG,
            )),
            SaladAny::Long(l) => Err(de::Error::invalid_type(de::Unexpected::Signed(*l), &ERR_MSG)),
            SaladAny::Float(f) => Err(de::Error::invalid_type(
                de::Unexpected::Float(*f as f64),
                &ERR_MSG,
            )),
            SaladAny::Double(d) => Err(de::Error::invalid_type(de::Unexpected::Float(*d), &ERR_MSG)),
            SaladAny::Object(_) => Err(de::Error::invalid_type(de::Unexpected::Map, &ERR_MSG)),
            SaladAny::List(_) => Err(de::Error::invalid_type(de::Unexpected::Seq, &ERR_MSG)),
        }
    }

    fn deserialize_map<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        static ERR_MSG: &str = "key-value map object";

        match self.0 {
            SaladAny::Object(o) => visitor.visit_map(SaladObjectMapAccess::new(o)),

            // Errors
            SaladAny::Bool(b) => Err(de::Error::invalid_type(de::Unexpected::Bool(*b), &ERR_MSG)),
            SaladAny::Int(i) => Err(de::Error::invalid_type(
                de::Unexpected::Signed(*i as i64),
                &ERR_MSG,
            )),
            SaladAny::Long(l) => Err(de::Error::invalid_type(de::Unexpected::Signed(*l), &ERR_MSG)),
            SaladAny::Float(f) => Err(de::Error::invalid_type(
                de::Unexpected::Float(*f as f64),
                &ERR_MSG,
            )),
            SaladAny::Double(d) => Err(de::Error::invalid_type(de::Unexpected::Float(*d), &ERR_MSG)),
            SaladAny::String(s) => Err(de::Error::invalid_type(de::Unexpected::Str(s), &ERR_MSG)),
            SaladAny::List(_) => Err(de::Error::invalid_type(de::Unexpected::Seq, &ERR_MSG)),
        }
    }

    fn deserialize_seq<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        static ERR_MSG: &str = "list of primitives/objects";

        match self.0 {
            SaladAny::List(l) => visitor.visit_seq(SaladAnyListSeqAccess::new(l)),

            // Errors
            SaladAny::Bool(b) => Err(de::Error::invalid_type(de::Unexpected::Bool(*b), &ERR_MSG)),
            SaladAny::Int(i) => Err(de::Error::invalid_type(
                de::Unexpected::Signed(*i as i64),
                &ERR_MSG,
            )),
            SaladAny::Long(l) => Err(de::Error::invalid_type(de::Unexpected::Signed(*l), &ERR_MSG)),
            SaladAny::Float(f) => Err(de::Error::invalid_type(
                de::Unexpected::Float(*f as f64),
                &ERR_MSG,
            )),
            SaladAny::Double(d) => Err(de::Error::invalid_type(de::Unexpected::Float(*d), &ERR_MSG)),
            SaladAny::String(s) => Err(de::Error::invalid_type(de::Unexpected::Str(s), &ERR_MSG)),
            SaladAny::Object(_) => Err(de::Error::invalid_type(de::Unexpected::Map, &ERR_MSG)),
        }
    }

    // Unimplemented methods with a default implementation
    serde::forward_to_deserialize_any! {
        i8 i16 u8 u16 u32 u64 char string bytes byte_buf option unit
        unit_struct newtype_struct tuple tuple_struct struct enum identifier ignored_any
    }
}

/// Map access implementation for SaladObject deserialization
pub(super) struct SaladObjectMapAccess<'de> {
    iter: hash_map::Iter<'de, CompactString, SaladAny>,
    value: Option<&'de SaladAny>,
}

impl<'de> SaladObjectMapAccess<'de> {
    pub fn new(obj: &'de SaladObject) -> Self {
        Self {
            iter: obj.map.iter(),
            value: None,
        }
    }
}

impl<'de> de::Deserializer<'de> for SaladObjectMapAccess<'de> {
    type Error = de::value::Error;

    fn deserialize_any<V>(self, visitor: V) -> Result<V::Value, Self::Error>
    where
        V: de::Visitor<'de>,
    {
        visitor.visit_map(self)
    }

    fn deserialize_map<V>(self, visitor: V) -> Result<V::Value, Self::Error>
    where
        V: de::Visitor<'de>,
    {
        visitor.visit_map(self)
    }

    // Forward all other methods to deserialize_any
    serde::forward_to_deserialize_any! {
        bool i8 i16 i32 i64 u8 u16 u32 u64 f32 f64 char str string bytes
        byte_buf option unit unit_struct newtype_struct seq tuple
        tuple_struct struct enum identifier ignored_any
    }
}

impl<'de> de::MapAccess<'de> for SaladObjectMapAccess<'de> {
    type Error = de::value::Error;

    fn next_key_seed<K>(&mut self, seed: K) -> Result<Option<K::Value>, Self::Error>
    where
        K: de::DeserializeSeed<'de>,
    {
        match self.iter.next() {
            Some((k, v)) => {
                self.value = Some(v);
                seed.deserialize(CompactStringDeserializer(k)).map(Some)
            }
            None => {
                self.value = None;
                Ok(None)
            }
        }
    }

    fn next_value_seed<V>(&mut self, seed: V) -> Result<V::Value, Self::Error>
    where
        V: de::DeserializeSeed<'de>,
    {
        let value = self.value.ok_or_else(|| de::Error::custom("value is missing"))?;
        seed.deserialize(SaladAnyDeserializer(value))
    }
}

/// Deserializer for CompactString values
struct CompactStringDeserializer<'de>(&'de CompactString);

impl<'de> de::Deserializer<'de> for CompactStringDeserializer<'de> {
    type Error = de::value::Error;

    fn deserialize_any<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        visitor.visit_borrowed_str(self.0.as_str())
    }

    fn deserialize_str<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        visitor.visit_borrowed_str(self.0.as_str())
    }

    fn deserialize_string<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        visitor.visit_string(self.0.to_string())
    }

    fn deserialize_bytes<V: de::Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error> {
        visitor.visit_borrowed_bytes(self.0.as_bytes())
    }

    fn deserialize_byte_buf<V>(self, visitor: V) -> Result<V::Value, Self::Error>
    where
        V: de::Visitor<'de>,
    {
        visitor.visit_byte_buf(self.0.as_bytes().to_vec())
    }

    fn deserialize_identifier<V>(self, visitor: V) -> Result<V::Value, Self::Error>
    where
        V: de::Visitor<'de>,
    {
        visitor.visit_borrowed_str(self.0.as_str())
    }

    // Forward all other methods to deserialize_any
    serde::forward_to_deserialize_any! {
        bool i8 i16 i32 i64 u8 u16 u32 u64 f32 f64 char option unit unit_struct
        newtype_struct seq tuple tuple_struct map struct enum ignored_any
    }
}

/// Sequence access implementation for SaladAny list deserialization
struct SaladAnyListSeqAccess<'de> {
    iter: slice::Iter<'de, SaladAny>,
}

impl<'de> SaladAnyListSeqAccess<'de> {
    pub fn new(list: &'de [SaladAny]) -> Self {
        Self { iter: list.iter() }
    }
}

impl<'de> de::SeqAccess<'de> for SaladAnyListSeqAccess<'de> {
    type Error = de::value::Error;

    fn next_element_seed<T>(&mut self, seed: T) -> Result<Option<T::Value>, Self::Error>
    where
        T: de::DeserializeSeed<'de>,
    {
        self.iter
            .next()
            .map(|v| seed.deserialize(SaladAnyDeserializer(v)))
            .transpose()
    }
}
