use std::ops::RangeInclusive;

mod macros;

pub(crate) use self::macros::impl_from_traits;
use crate::primitive::{SaladDouble, SaladFloat, SaladInt, SaladLong};

/// Range representing the minimum and maximum [SaladLong]
/// values that can be stored in a [SaladInt].
pub(crate) const INT_RANGE: RangeInclusive<SaladLong> =
    (SaladInt::MIN as SaladLong)..=(SaladInt::MAX as SaladLong);

/// Range representing the minimum and maximum [SaladDouble]
/// values that can be stored in a [SaladFloat].
pub(crate) const FLOAT_RANGE: RangeInclusive<SaladDouble> =
    (SaladFloat::MIN as SaladDouble)..=(SaladFloat::MAX as SaladDouble);
