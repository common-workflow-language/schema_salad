using OneOf;
using YamlDotNet.Serialization;

namespace ${project_name};

public class RootLoader
{
    public static ${root_loader_type} LoadDocument(in Dictionary<object, object> doc, in string baseUri_, in LoadingOptions? loadingOptions_ = null)
    {
        string baseUri = EnsureBaseUri(baseUri_);
        LoadingOptions loadingOptions;

        if (loadingOptions_ == null)
        {
            loadingOptions = new LoadingOptions(fileUri: baseUri);
        }
        else
        {
            loadingOptions = loadingOptions_;
        }

        dynamic outDoc = LoaderInstances.${root_loader}.DocumentLoad(doc, baseUri, loadingOptions);
        return outDoc;
    }

    public static ${root_loader_type} LoadDocument(in string doc, in string uri_, in LoadingOptions? loadingOptions_ = null)
    {
        string uri = EnsureBaseUri(uri_);
        LoadingOptions loadingOptions;

        if (loadingOptions_ == null)
        {
            loadingOptions = new LoadingOptions(fileUri: uri);
        }
        else
        {
            loadingOptions = loadingOptions_;
        }

        IDeserializer deserializer = new DeserializerBuilder().WithNodeTypeResolver(new ScalarNodeTypeResolver()).Build();
        object? yamlObject = deserializer.Deserialize(new StringReader(doc));
        loadingOptions.idx.Add(uri, yamlObject!);
        return LoadDocument((Dictionary<object, object>)yamlObject!, uri, loadingOptions);
    }

    static string EnsureBaseUri(in string baseUri_)
    {
        string baseUri = baseUri_;
        if (baseUri == null)
        {
            baseUri = new Uri(Environment.CurrentDirectory).AbsoluteUri;
        }

        return baseUri;
    }
}
