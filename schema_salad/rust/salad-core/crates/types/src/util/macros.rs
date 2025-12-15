macro_rules! impl_from_traits {
    (
        $ty:ident {
            $( $ident:ident => $subty:ident ),* $(,)?
        }
    ) => {
        $(
            impl From<$subty> for $ty {
                #[inline]
                fn from(value: $subty) -> Self {
                    Self::$ident(value)
                }
            }

            impl TryFrom<$ty> for $subty {
                type Error = $ty;

                fn try_from(value: $ty) -> Result<Self, Self::Error> {
                    match value {
                        $ty::$ident(v) => Ok(v),
                        _ => Err(value),
                    }
                }
            }

            impl<'a> TryFrom<&'a $ty> for &'a $subty {
                type Error = &'a $ty;

                fn try_from(value: &'a $ty) -> Result<Self, Self::Error> {
                    match value {
                        $ty::$ident(v) => Ok(v),
                        _ => Err(value),
                    }
                }
            }
        )*
    };
}

pub(crate) use impl_from_traits;
