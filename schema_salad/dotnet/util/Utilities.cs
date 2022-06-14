namespace ${project_name};

public static class Utilities
{
    /**
     * Compute the shortname of a fully qualified identifer.
     * See https://w3id.org/cwl/v1.2/SchemaSalad.html#Short_names. 
     *
     */
    public static string Shortname(string inputId)
    {
        Uri parsedId = new(inputId);
        if (parsedId.IsAbsoluteUri && parsedId.Fragment != "")
        {
            string[] fragmentSplit = parsedId.FragmentWithoutFragmentation().Split('/');
            return fragmentSplit[fragmentSplit.Length - 1];
        }
        else if (parsedId.IsAbsoluteUri && parsedId.AbsolutePath != null)
        {
            string[] pathSplit = parsedId.AbsolutePath.Split('/');
            return pathSplit[pathSplit.Length - 1];
        }
        else
        {
            return inputId;
        }
    }
}

public interface IEnumClass
{

}

public interface IEnumClass<T> : IEnumClass
{
    public abstract static T Parse(string value);
    public abstract static bool Contains(string value);
    public abstract static List<string> Symbols();
}