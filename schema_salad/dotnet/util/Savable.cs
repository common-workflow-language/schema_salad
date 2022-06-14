using System.Collections;

namespace ${project_name};

public interface ISavable
{
    public static abstract ISavable FromDoc(object doc, string baseUri, LoadingOptions loadingOptions, string? docRoot = null);
    public abstract Dictionary<object, object> Save(bool top, string baseUrl, bool relativeUris);

    public static object Save(object val, bool top = true, string baseurl = "", bool relativeUris = true)
    {
        if (val is ISavable valSaveable)
        {
            return valSaveable.Save(top, baseurl, relativeUris);
        }

        if (val is IList)
        {
            List<object> r = new();
            List<object> valList = (List<object>)val;
            foreach (object v in valList)
            {
                r.Add(Save(v, false, baseurl, relativeUris));
            }

            return r;
        }

        if (val is IDictionary)
        {
            Dictionary<object, object> valDict = (Dictionary<object, object>)val;
            Dictionary<object, object> newDict = new();
            foreach (KeyValuePair<object, object> entry in valDict)
            {
                newDict[entry.Key] = Save(entry.Value, false, baseurl, relativeUris);
            }

            return newDict;
        }

        return val;
    }

    public static object SaveRelativeUri(object uri, bool scopedId, bool relativeUris, int? refScope, string baseUrl = "")
    {
        if (relativeUris == false || (uri is string @string && @string == baseUrl))
        {
            return uri;
        }

        if (uri is IList)
        {
            List<object> uriList = (List<object>)uri;
            List<object> r = new();
            foreach (object v in uriList)
            {
                r.Add(SaveRelativeUri(v, scopedId, relativeUris, refScope, baseUrl));
            }

            return r;
        }
        else if (uri is string uriString)
        {
            Uri uriSplit = new(uriString, UriKind.RelativeOrAbsolute);
            Uri baseSplit = new(baseUrl, UriKind.RelativeOrAbsolute);
            if ((!uriSplit.IsAbsoluteUri && !baseSplit.IsAbsoluteUri) || (uriSplit.IsAbsoluteUri && uriSplit.AbsolutePath.Length < 1)
                || (baseSplit.IsAbsoluteUri && baseSplit.AbsolutePath.Length < 1))
            {
                throw new ValidationException("Uri or baseurl need to contain a path");
            }

            if (uriSplit.IsAbsoluteUri && baseSplit.IsAbsoluteUri && uriSplit.Scheme == baseSplit.Scheme && uriSplit.Host == baseSplit.Host)
            {
                if (uriSplit.AbsolutePath != baseSplit.AbsolutePath)
                {
                    string p = Path.GetRelativePath(Path.GetDirectoryName(baseSplit.AbsolutePath)!, uriSplit.AbsolutePath);
                    if (uriSplit.Fragment.Length > 0)
                    {
                        p = p + "#" + uriSplit.FragmentWithoutFragmentation();
                    }

                    return p;
                }

                string baseFrag = baseSplit.FragmentWithoutFragmentation() + "/";
                if (refScope != null)
                {
                    List<string> sp = baseFrag.Split('/').ToList();
                    int i = 0;
                    while (i < refScope)
                    {
                        sp.RemoveAt(sp.Count - 1);
                        i += 1;
                    }

                    baseFrag = string.Join('/', sp);
                }

                if (uriSplit.FragmentWithoutFragmentation().StartsWith(baseFrag))
                {
                    return uriSplit.FragmentWithoutFragmentation().Substring(baseFrag.Length);
                }
                else
                {
                    return uriSplit.FragmentWithoutFragmentation();
                }
            }
            else
            {
                return Save(uri, false, baseUrl);
            }

        }

        throw new ValidationException("uri needs to be of type List or String");
    }
}
