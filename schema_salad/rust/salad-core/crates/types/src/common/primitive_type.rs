use std::fmt;

use serde::{de, ser};

use crate::SaladType;

/// Names of salad data primitive types (based on Avro schema declarations).
///
/// Refer to the [Avro schema declaration documentation](https://avro.apache.org/docs/++version++/specification/#primitive-types)
/// for detailed information.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PrimitiveType {
    /// No value.
    ///
    /// Matches constant value `null`.
    Null,
    /// A binary value.
    ///
    /// Matches constant value `boolean`.
    Boolean,
    /// 32-bit signed integer.
    ///
    /// Matches constant value `int`.
    Int,
    /// 64-bit signed integer.
    ///
    /// Matches constant value `long`.
    Long,
    /// Single precision (32-bit) IEEE 754 floating-point number.
    ///
    /// Matches constant value `float`.
    Float,
    /// Double precision (64-bit) IEEE 754 floating-point number.
    ///
    /// Matches constant value `double`.
    Double,
    /// Unicode character sequence.
    ///
    /// Matches constant value `string`.
    String,
}

impl SaladType for PrimitiveType {}

impl fmt::Display for PrimitiveType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str({
            match self {
                Self::Null => "null",
                Self::Boolean => "boolean",
                Self::Int => "int",
                Self::Long => "long",
                Self::Float => "float",
                Self::Double => "double",
                Self::String => "string",
            }
        })
    }
}

impl ser::Serialize for PrimitiveType {
    #[inline]
    fn serialize<S: ser::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.collect_str(self)
    }
}

impl<'de> de::Deserialize<'de> for PrimitiveType {
    fn deserialize<D: de::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct PrimitiveTypeVisitor;

        impl de::Visitor<'_> for PrimitiveTypeVisitor {
            type Value = PrimitiveType;

            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str(
                    "any of the following strings: `null`, `boolean`, `int`, `long`, `float`, `double`, `string`"
                )
            }

            fn visit_str<E: de::Error>(self, v: &str) -> Result<Self::Value, E> {
                match v {
                    "null" => Ok(PrimitiveType::Null),
                    "boolean" => Ok(PrimitiveType::Boolean),
                    "int" => Ok(PrimitiveType::Int),
                    "long" => Ok(PrimitiveType::Long),
                    "float" => Ok(PrimitiveType::Float),
                    "double" => Ok(PrimitiveType::Double),
                    "string" => Ok(PrimitiveType::String),
                    _ => Err(de::Error::invalid_value(
                        de::Unexpected::Str(v),
                        &self,
                    )),
                }
            }
        }

        deserializer.deserialize_str(PrimitiveTypeVisitor)
    }
}
