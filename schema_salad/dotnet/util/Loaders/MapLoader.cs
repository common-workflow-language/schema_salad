using System.Collections;

namespace ${project_name};

internal class MapLoader<T> : ILoader<Dictionary<string, T>>
{
    private readonly ILoader valueLoader;

    public MapLoader(in ILoader valueLoader)
    {
        this.valueLoader = valueLoader;
    }

    public Dictionary<string, T> Load(in object doc, in string baseuri, in LoadingOptions loadingOptions, in string? docRoot = null)
    {
        if (doc == null)
        {
            throw new ValidationException("Expected non null");
        }

        if (doc is not IDictionary)
        {
            throw new ValidationException("Expected list");
        }

        IDictionary docDictionary = (IDictionary)doc;
        Dictionary<string, T> returnValue = new();
        List<ILoader> loaders = new()
        {
            this,
            valueLoader
        };
        ILoader<object> unionLoader = new UnionLoader(loaders);
        List<ValidationException> errors = new();

        foreach (KeyValuePair<string, T> item in docDictionary)
        {
            try
            {
                dynamic loadedField = unionLoader.LoadField(item.Value, baseuri, loadingOptions);
                returnValue[item.Key] = loadedField;
            }
            catch (ValidationException e)
            {
                errors.Add(e);
            }
        }

        if (errors.Count > 0)
        {
            throw new ValidationException("", errors);
        }

        return returnValue;
    }

    object ILoader.Load(in object doc, in string baseuri, in LoadingOptions loadingOptions, in string? docRoot)
    {
        return Load(doc, baseuri, loadingOptions, docRoot);
    }
}
