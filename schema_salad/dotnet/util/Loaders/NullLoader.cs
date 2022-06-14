namespace ${project_name};
internal class NullLoader : ILoader<object>
{
    public object Load(in object doc, in string baseuri, in LoadingOptions loadingOptions, in string? docRoot = null)
    {
        if (doc != null)
        {
            throw new ValidationException("Expected null");
        }

        return doc!;
    }
}
