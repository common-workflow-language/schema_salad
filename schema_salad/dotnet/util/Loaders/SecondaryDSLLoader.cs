using System.Collections;

namespace ${project_name};

internal class SecondaryDSLLoader<T> : ILoader<T>
{
    readonly ILoader<T> inner;

    public SecondaryDSLLoader(ILoader<T> inner)
    {
        this.inner = inner;
    }

    public T Load(in object doc_, in string baseuri, in LoadingOptions loadingOptions, in string? docRoot = null)
    {
        List<Dictionary<string, object>> r = new();
        object doc = doc_;
        if (doc is IList)
        {
            List<object> docList = (List<object>)doc;
            foreach (object d in docList)
            {
                Dictionary<string, object> entry = new();
                if (d is string dString)
                {
                    if (dString.EndsWith("?"))
                    {
                        entry.Add("pattern", dString.Substring(0, dString.Length - 1));
                        entry.Add("required", false);

                    }
                    else
                    {
                        entry.Add("pattern", dString);
                    }

                    r.Add(entry);
                }
                else if (d is IDictionary)
                {
                    Dictionary<string, object> dMap = new((Dictionary<string, object>)d);
                    if (dMap.ContainsKey("pattern"))
                    {
                        entry.Add("pattern", dMap["pattern"]);
                        dMap.Remove("pattern");
                    }
                    else
                    {
                        throw new ValidationException("Missing 'pattern' in secondaryFiles specification entry.");
                    }

                    if (dMap.ContainsKey("required"))
                    {
                        entry.Add("required", dMap["required"]);
                        dMap.Remove("required");
                    }

                    if (dMap.Count > 0)
                    {
                        throw new ValidationException("Unallowed values in secondaryFiles specification entry");
                    }

                    r.Add(entry);
                }
                else
                {
                    throw new ValidationException("Expected a string or sequence of (strings or mappings).");
                }
            }
        }
        else if (doc is IDictionary)
        {
            Dictionary<string, object> entry = new();
            Dictionary<string, object> dMap = new((Dictionary<string, object>)doc);
            if (dMap.ContainsKey("pattern"))
            {
                entry.Add("pattern", dMap["pattern"]);
                dMap.Remove("pattern");
            }
            else
            {
                throw new ValidationException("Missing 'pattern' in secondaryFiles specification entry.");
            }

            if (dMap.ContainsKey("required"))
            {
                entry.Add("required", dMap["required"]);
                dMap.Remove("required");
            }

            if (dMap.Count > 0)
            {
                throw new ValidationException("Unallowed values in secondaryFiles specification entry.");
            }

            r.Add(entry);
        }
        else if (doc is string dString)
        {
            Dictionary<string, object> entry = new();
            if (dString.EndsWith("?"))
            {
                entry.Add("pattern", dString.Substring(0, dString.Length - 1));
                entry.Add("required", false);
            }
            else
            {
                entry.Add("pattern", dString);
            }

            r.Add(entry);
        }
        else
        {
            throw new ValidationException("Expected a string or sequence of (strings or mappings).");
        }

        return inner.Load(r, baseuri, loadingOptions, docRoot);
    }

    object ILoader.Load(in object doc, in string baseuri, in LoadingOptions loadingOptions, in string? docRoot)
    {
        return Load(doc,
                    baseuri,
                    loadingOptions,
                    docRoot)!;
    }
}
