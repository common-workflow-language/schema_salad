use std::marker::PhantomData;
use serde::de;

use salad_types::SaladType;

mod data;
mod list;
mod map;

use self::list::SingleOrManySeed;
pub use self::{data::SeedData, map::MapToListSeed};

/// Represents a type that can be converted into a serde
/// [`DeserializeSeed`](serde::de::DeserializeSeed).
pub trait IntoDeserializeSeed<'de, 'sd> {
    type DeserializeSeed: de::DeserializeSeed<'de, Value = Self>;

    /// Returns a
    /// [`DeserializeSeed`](https://docs.rs/serde/latest/serde/de/trait.DeserializeSeed.html)
    /// instance from a [`SeedData`] reference that's able to deserialize this type.
    fn deserialize_seed(data: &'sd SeedData) -> Self::DeserializeSeed;
}

impl<'de, 'sd, T> IntoDeserializeSeed<'de, 'sd> for Box<[T]>
where
    T: SaladType + IntoDeserializeSeed<'de, 'sd>,
{
    type DeserializeSeed = SingleOrManySeed<'sd, T>;

    #[inline]
    fn deserialize_seed(data: &'sd SeedData) -> Self::DeserializeSeed {
        SingleOrManySeed {
            data,
            _phant: PhantomData,
        }
    }
}

macro_rules! impl_default_intoseed {
    ( $( $ty:path ),* $(,)? ) => {
        $(
            impl<'sd> IntoDeserializeSeed<'_, 'sd> for $ty {
                type DeserializeSeed = std::marker::PhantomData<Self>;

                #[inline]
                fn deserialize_seed(_: &'sd SeedData) -> Self::DeserializeSeed {
                    std::marker::PhantomData
                }
            }
        )*
    };
}

impl_default_intoseed! {
    // Any & Object
    salad_types::SaladAny,
    salad_types::SaladObject,

    // Primitives
    salad_types::SaladBool,
    salad_types::SaladInt,
    salad_types::SaladLong,
    salad_types::SaladFloat,
    salad_types::SaladDouble,
    salad_types::SaladString,
    salad_types::SaladPrimitive,

    // Common
    salad_types::common::ArrayName,
    salad_types::common::EnumName,
    salad_types::common::RecordName,
    salad_types::common::PrimitiveType,
}
