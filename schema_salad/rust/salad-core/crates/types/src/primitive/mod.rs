use std::fmt;

use serde::{de, ser};

mod string;

pub use self::string::SaladString;
use crate::{
    util::{FLOAT_RANGE, INT_RANGE},
    SaladType,
};

/// A binary value.
pub type SaladBool = bool;
impl SaladType for SaladBool {}

/// 32-bit signed integer.
pub type SaladInt = i32;
impl SaladType for SaladInt {}

/// 64-bit signed integer.
pub type SaladLong = i64;
impl SaladType for SaladLong {}

/// Single precision (32-bit) IEEE 754 floating-point number.
pub type SaladFloat = f32;
impl SaladType for SaladFloat {}

/// Double precision (64-bit) IEEE 754 floating-point number.
pub type SaladDouble = f64;
impl SaladType for SaladDouble {}

/// Schema Salad primitives, except `null`.
#[derive(Debug, Clone, PartialEq, PartialOrd)]
pub enum SaladPrimitive {
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
}

impl SaladType for SaladPrimitive {}

crate::util::impl_from_traits! {
    SaladPrimitive {
        Bool => SaladBool,
        Int => SaladInt,
        Long => SaladLong,
        Float => SaladFloat,
        Double => SaladDouble,
        String => SaladString,
    }
}

impl fmt::Display for SaladPrimitive {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Bool(b) => fmt::Display::fmt(b, f),
            Self::Int(i) => fmt::Display::fmt(i, f),
            Self::Long(l) => fmt::Display::fmt(l, f),
            Self::Float(fl) => fmt::Display::fmt(fl, f),
            Self::Double(d) => fmt::Display::fmt(d, f),
            Self::String(s) => fmt::Display::fmt(s, f),
        }
    }
}

impl ser::Serialize for SaladPrimitive {
    fn serialize<S: ser::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        match self {
            Self::Bool(b) => serializer.serialize_bool(*b),
            Self::Int(i) => serializer.serialize_i32(*i),
            Self::Long(l) => serializer.serialize_i64(*l),
            Self::Float(f) => serializer.serialize_f32(*f),
            Self::Double(d) => serializer.serialize_f64(*d),
            Self::String(s) => serializer.serialize_str(s),
        }
    }
}

impl<'de> de::Deserialize<'de> for SaladPrimitive {
    fn deserialize<D: de::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct SaladPrimitiveVisitor;

        impl de::Visitor<'_> for SaladPrimitiveVisitor {
            type Value = SaladPrimitive;

            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("any of the salad primitives")
            }
            fn visit_bool<E: de::Error>(self, v: bool) -> Result<Self::Value, E> {
                Ok(SaladPrimitive::Bool(v))
            }

            fn visit_i8<E: de::Error>(self, v: i8) -> Result<Self::Value, E> {
                Ok(SaladPrimitive::Int(v as i32))
            }

            fn visit_i16<E: de::Error>(self, v: i16) -> Result<Self::Value, E> {
                Ok(SaladPrimitive::Int(v as i32))
            }

            fn visit_i32<E: de::Error>(self, v: i32) -> Result<Self::Value, E> {
                Ok(SaladPrimitive::Int(v))
            }

            fn visit_i64<E: de::Error>(self, v: i64) -> Result<Self::Value, E> {
                match v {
                    l if INT_RANGE.contains(&l) => Ok(SaladPrimitive::Int(v as i32)),
                    _ => Ok(SaladPrimitive::Long(v)),
                }
            }

            fn visit_u8<E: de::Error>(self, v: u8) -> Result<Self::Value, E> {
                Ok(SaladPrimitive::Int(v as i32))
            }

            fn visit_u16<E: de::Error>(self, v: u16) -> Result<Self::Value, E> {
                Ok(SaladPrimitive::Int(v as i32))
            }

            fn visit_u64<E: de::Error>(self, v: u64) -> Result<Self::Value, E> {
                match v {
                    u if u <= i32::MAX as u64 => Ok(SaladPrimitive::Int(v as i32)),
                    u if u <= i64::MAX as u64 => Ok(SaladPrimitive::Long(v as i64)),
                    _ => Err(de::Error::invalid_value(de::Unexpected::Unsigned(v), &self)),
                }
            }

            fn visit_f32<E: de::Error>(self, v: f32) -> Result<Self::Value, E> {
                Ok(SaladPrimitive::Float(v))
            }

            fn visit_f64<E: de::Error>(self, v: f64) -> Result<Self::Value, E> {
                match v {
                    d if FLOAT_RANGE.contains(&d) => Ok(SaladPrimitive::Float(v as f32)),
                    _ => Ok(SaladPrimitive::Double(v)),
                }
            }

            fn visit_str<E: de::Error>(self, v: &str) -> Result<Self::Value, E> {
                Ok(SaladPrimitive::String(v.into()))
            }

            fn visit_string<E: de::Error>(self, v: String) -> Result<Self::Value, E> {
                Ok(SaladPrimitive::String(v.into()))
            }

            fn visit_bytes<E: de::Error>(self, v: &[u8]) -> Result<Self::Value, E> {
                match std::str::from_utf8(v) {
                    Ok(s) => Ok(SaladPrimitive::String(s.into())),
                    Err(_) => Err(de::Error::invalid_value(de::Unexpected::Bytes(v), &self)),
                }
            }
        }

        deserializer.deserialize_any(SaladPrimitiveVisitor)
    }
}
