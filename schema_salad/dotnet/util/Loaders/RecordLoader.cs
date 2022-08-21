using System.Collections;

namespace ${project_name};

internal class RecordLoader<T> : ILoader<T> where T : ISaveable
{
    public T Load(in object doc, in string baseUri, in LoadingOptions loadingOptions, in string? docRoot = null)
    {
        if (doc is not IDictionary)
        {
            throw new ValidationException($"Expected object with type of Dictionary but got {doc.GetType()}");
        }

        return (T)T.FromDoc(doc, baseUri, loadingOptions, docRoot);
    }

    object ILoader.Load(in object doc, in string baseuri, in LoadingOptions loadingOptions, in string? docRoot)
    {
        return Load(doc,
                    baseuri,
                    loadingOptions,
                    docRoot)!;
    }
}

