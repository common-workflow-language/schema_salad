using LanguageExt;

namespace ${project_name};

internal class OptionalLoader<T> : ILoader<Option<T>>
{
    readonly ILoader<T> innerLoader;

    public OptionalLoader(ILoader<T> innerLoader) {
        this.innerLoader = innerLoader;
    }

    public object Load(in object doc, in string baseuri, in LoadingOptions loadingOptions, in string? docRoot = null)
    {
        return Load(doc, baseuri, loadingOptions, docRoot);
    }

    Option<T> ILoader<Option<T>>.Load(in object doc, in string baseuri, in LoadingOptions loadingOptions, in string? docRoot)
    {
        if(doc == null){
            return Option<T>.None;
        }

        return Option<T>.Some(innerLoader.Load(doc,baseuri,loadingOptions,docRoot));
    }
}
