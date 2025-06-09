use std::fmt;
use std::convert::TryFrom;

use serde::{de as des, ser};

mod de;
mod object;

pub use self::object::SaladObject;
use crate::{
    primitive::{SaladBool, SaladDouble, SaladFloat, SaladInt, SaladLong, SaladString},
    util::{FLOAT_RANGE, INT_RANGE},
    SaladType,
};

/// The `SaladAny` type validates for any non-null value.
#[derive(Debug, Clone, PartialEq)]
pub enum SaladAny {
    /// A binary value.
    Bool(SaladBool),
    /// 32-bit signed integer.
    Int(SaladInt),
    /// 64-bit signed integer.
    Long(SaladLong),
    /// Single precision (32-bit) IEEE 754 floating-point number.
    Float(SaladFloat),
    /// Double precision (64-bit) IEEE 754 floating-point number.
    Double(SaladDouble),
    /// Unicode character sequence.
    String(SaladString),
    /// Unknown object.
    Object(SaladObject),
    /// List of any values.
    List(Box<[SaladAny]>),
}

impl SaladAny {
    /// Attempts to downcast to type `T` from a borrowed `SaladAny`.
    /// N.B. When downcasting to a primitive (or object) type, consider using
    /// a `match` expression or the `TryFrom::try_from` method.
    pub fn downcast<'de, T>(&'de self) -> Result<T, &'de Self>
    where
        T: SaladType + des::Deserialize<'de>,
    {
        let deserializer = self::de::SaladAnyDeserializer(self);
        T::deserialize(deserializer).map_err(|_| self)
    }

    /// Attempts to downcast from a consumed `SaladAny` to type `T`.
    /// N.B. When downcasting to a primitive (or object) type, consider using
    /// a `match` expression or the `TryFrom::try_from` method.
    #[inline]
    pub fn downcast_into<T>(self) -> Result<T, Self>
    where
        for<'de> T: SaladType + des::Deserialize<'de>,
    {
        // Avoid duplicating the deserialization logic
        match Self::downcast(&self) {
            Ok(t) => Ok(t),
            Err(_) => Err(self),
        }
    }

    /// Returns true if this value is a boolean
    #[inline]
    pub fn is_bool(&self) -> bool {
        matches!(self, Self::Bool(_))
    }

    /// Returns true if this value is an integer (Int or Long)
    #[inline]
    pub fn is_integer(&self) -> bool {
        matches!(self, Self::Int(_) | Self::Long(_))
    }

    /// Returns true if this value is a floating point number (Float or Double)
    #[inline]
    pub fn is_float(&self) -> bool {
        matches!(self, Self::Float(_) | Self::Double(_))
    }

    /// Returns true if this value is a string
    #[inline]
    pub fn is_string(&self) -> bool {
        matches!(self, Self::String(_))
    }

    /// Returns true if this value is an object
    #[inline]
    pub fn is_object(&self) -> bool {
        matches!(self, Self::Object(_))
    }

    /// Returns true if this value is a list
    #[inline]
    pub fn is_list(&self) -> bool {
        matches!(self, Self::List(_))
    }
}

impl SaladType for SaladAny {}

crate::util::impl_from_traits! {
    SaladAny {
        Bool => SaladBool,
        Int => SaladInt,
        Long => SaladLong,
        Float => SaladFloat,
        Double => SaladDouble,
        String => SaladString,
        Object => SaladObject,
    }
}

impl<T> From<Vec<T>> for SaladAny
where
    T: SaladType,
    Self: From<T>,
{
    fn from(value: Vec<T>) -> Self {
        let list = value.into_iter().map(Self::from).collect();
        Self::List(list)
    }
}

impl<T> From<Box<[T]>> for SaladAny
where
    T: SaladType,
    Self: From<Vec<T>>,
{
    #[inline]
    fn from(value: Box<[T]>) -> Self {
        Self::from(value.into_vec())
    }
}

impl ser::Serialize for SaladAny {
    fn serialize<S: ser::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        match self {
            Self::Bool(b) => serializer.serialize_bool(*b),
            Self::Int(i) => serializer.serialize_i32(*i),
            Self::Long(l) => serializer.serialize_i64(*l),
            Self::Float(f) => serializer.serialize_f32(*f),
            Self::Double(d) => serializer.serialize_f64(*d),
            Self::String(s) => s.serialize(serializer),
            Self::Object(o) => o.serialize(serializer),
            Self::List(l) => l.serialize(serializer),
        }
    }
}

impl<'de> des::Deserialize<'de> for SaladAny {
    fn deserialize<D: des::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct SaladAnyVisitor;

        impl<'de> des::Visitor<'de> for SaladAnyVisitor {
            type Value = SaladAny;

            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("a salad primitive, a key-value object, or a list of them")
            }

            fn visit_bool<E: des::Error>(self, v: bool) -> Result<Self::Value, E> {
                Ok(SaladAny::Bool(v))
            }

            fn visit_i8<E: des::Error>(self, v: i8) -> Result<Self::Value, E> {
                Ok(SaladAny::Int(v.into()))
            }

            fn visit_i16<E: des::Error>(self, v: i16) -> Result<Self::Value, E> {
                Ok(SaladAny::Int(v.into()))
            }

            fn visit_i32<E: des::Error>(self, v: i32) -> Result<Self::Value, E> {
                Ok(SaladAny::Int(v))
            }

            fn visit_i64<E: des::Error>(self, v: i64) -> Result<Self::Value, E> {
                if INT_RANGE.contains(&v) {
                    Ok(SaladAny::Int(v as i32))
                } else {
                    Ok(SaladAny::Long(v))
                }
            }

            fn visit_u8<E: des::Error>(self, v: u8) -> Result<Self::Value, E> {
                Ok(SaladAny::Int(v.into()))
            }

            fn visit_u16<E: des::Error>(self, v: u16) -> Result<Self::Value, E> {
                Ok(SaladAny::Int(v.into()))
            }

            fn visit_u32<E: des::Error>(self, v: u32) -> Result<Self::Value, E> {
                if v <= i32::MAX as u32 {
                    Ok(SaladAny::Int(v as i32))
                } else {
                    Ok(SaladAny::Long(v.into()))
                }
            }

            fn visit_u64<E: des::Error>(self, v: u64) -> Result<Self::Value, E> {
                if v <= i32::MAX as u64 {
                    Ok(SaladAny::Int(v as i32))
                } else if v <= i64::MAX as u64 {
                    Ok(SaladAny::Long(v as i64))
                } else {
                    Err(des::Error::invalid_value(
                        des::Unexpected::Unsigned(v),
                        &self,
                    ))
                }
            }

            fn visit_f32<E: des::Error>(self, v: f32) -> Result<Self::Value, E> {
                Ok(SaladAny::Float(v))
            }

            fn visit_f64<E: des::Error>(self, v: f64) -> Result<Self::Value, E> {
                if FLOAT_RANGE.contains(&v) {
                    Ok(SaladAny::Float(v as f32))
                } else {
                    Ok(SaladAny::Double(v))
                }
            }

            fn visit_str<E: des::Error>(self, v: &str) -> Result<Self::Value, E> {
                Ok(SaladAny::String(v.into()))
            }

            fn visit_string<E: des::Error>(self, v: String) -> Result<Self::Value, E> {
                Ok(SaladAny::String(v.into()))
            }

            fn visit_bytes<E: des::Error>(self, v: &[u8]) -> Result<Self::Value, E> {
                match core::str::from_utf8(v) {
                    Ok(s) => Ok(SaladAny::String(s.into())),
                    Err(_) => Err(des::Error::invalid_value(des::Unexpected::Bytes(v), &self)),
                }
            }

            fn visit_map<A>(self, map: A) -> Result<Self::Value, A::Error>
            where
                A: des::MapAccess<'de>,
            {
                let deserializer = des::value::MapAccessDeserializer::new(map);
                <SaladObject as des::Deserialize>::deserialize(deserializer).map(SaladAny::Object)
            }

            fn visit_seq<A>(self, seq: A) -> Result<Self::Value, A::Error>
            where
                A: des::SeqAccess<'de>,
            {
                let deserializer = des::value::SeqAccessDeserializer::new(seq);
                <Box<[SaladAny]> as des::Deserialize>::deserialize(deserializer).map(SaladAny::List)
            }

            fn visit_none<E: des::Error>(self) -> Result<Self::Value, E> {
                Err(des::Error::invalid_type(des::Unexpected::Option, &self))
            }

            fn visit_unit<E: des::Error>(self) -> Result<Self::Value, E> {
                Err(des::Error::invalid_type(des::Unexpected::Unit, &self))
            }
        }

        deserializer.deserialize_any(SaladAnyVisitor)
    }
}
