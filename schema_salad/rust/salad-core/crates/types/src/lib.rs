use std::sync::Arc;

mod any;
pub mod common;
mod primitive;
mod util;

pub use self::{
    any::{SaladAny, SaladObject},
    primitive::{
        SaladBool, SaladDouble, SaladFloat, SaladInt, SaladLong, SaladPrimitive, SaladString,
    },
};

/// A marker trait for Schema Salad data types.
///
/// This trait is implemented by all types that represent valid Schema Salad data,
/// including primitives (boolean, int, float, string), objects, and collections.
pub trait SaladType: Sized {}

impl<T: SaladType> SaladType for Arc<T> {}
impl<T: SaladType> SaladType for Arc<[T]> {}

impl<T: SaladType> SaladType for Vec<T> {}
impl<T: SaladType> SaladType for Box<[T]> {}

#[cfg(test)]
mod tests {
    use crate::{primitive, SaladAny, SaladObject};

    #[test]
    fn test_deserialize_bool() {
        let yaml = "true";
        let any = serde_yaml_ng::from_str::<SaladAny>(yaml).unwrap();
        let b = any.downcast::<primitive::SaladBool>().unwrap();
        assert!(b);
    }

    #[test]
    fn test_deserialize_int() {
        let yaml = "42";
        let any = serde_yaml_ng::from_str::<SaladAny>(yaml).unwrap();
        let i = any.downcast::<primitive::SaladLong>().unwrap();
        assert_eq!(i, 42);
    }

    #[test]
    fn test_deserialize_float() {
        let yaml = "3.14";
        let any = serde_yaml_ng::from_str::<SaladAny>(yaml).unwrap();
        let f = any.downcast::<primitive::SaladDouble>().unwrap();
        assert_eq!((f * 100.0).round(), 314.0);
    }

    #[test]
    fn test_deserialize_string() {
        let yaml = "hello world";
        let any = serde_yaml_ng::from_str::<SaladAny>(yaml).unwrap();
        let s = any.downcast::<primitive::SaladString>().unwrap();
        assert_eq!(s, "hello world");
    }

    #[test]
    fn test_deserialize_primitive() {
        let yaml = "42";
        let any = serde_yaml_ng::from_str::<SaladAny>(yaml).unwrap();
        let primitive = any.downcast::<primitive::SaladPrimitive>().unwrap();
        assert_eq!(primitive.to_string(), "42");

        let yaml = "true";
        let any = serde_yaml_ng::from_str::<SaladAny>(yaml).unwrap();
        let primitive = any.downcast::<primitive::SaladPrimitive>().unwrap();
        assert_eq!(primitive.to_string(), "true");

        let yaml = "3.14";
        let any = serde_yaml_ng::from_str::<SaladAny>(yaml).unwrap();
        let primitive = any.downcast::<primitive::SaladPrimitive>().unwrap();
        assert_eq!(primitive.to_string(), "3.14");

        let yaml = "hello";
        let any = serde_yaml_ng::from_str::<SaladAny>(yaml).unwrap();
        let primitive = any.downcast::<primitive::SaladPrimitive>().unwrap();
        assert_eq!(primitive.to_string(), "hello");
    }

    #[test]
    fn test_deserialize_object() {
        let yaml = r#"
            name: John
            age: 30
            likes_pizza: true
        "#;
        let any = serde_yaml_ng::from_str::<SaladAny>(yaml).unwrap();
        let obj: SaladObject = any.downcast().unwrap();

        assert_eq!(
            obj.get("name")
                .unwrap()
                .downcast::<primitive::SaladString>()
                .unwrap(),
            "John"
        );
        assert_eq!(
            obj.get("age")
                .unwrap()
                .downcast::<primitive::SaladInt>()
                .unwrap(),
            30
        );
        assert!(obj
            .get("likes_pizza")
            .unwrap()
            .downcast::<primitive::SaladBool>()
            .unwrap());
    }

    #[test]
    fn test_failed_downcast() {
        let yaml = "42";
        let any = serde_yaml_ng::from_str::<SaladAny>(yaml).unwrap();
        assert!(any.downcast::<primitive::SaladString>().is_err());
    }
}
