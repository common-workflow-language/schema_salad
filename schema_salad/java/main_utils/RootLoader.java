package ${package}.utils;

import java.nio.file.Paths;
import java.util.Map;


public class RootLoader {
    public static ${root_loader_instance_type} loadDocument(final Map<String, Object> doc, final String baseUri_, final LoadingOptions loadingOptions_) {
        String baseUri = baseUri_;
        if(baseUri == null) {
            baseUri = Uris.fileUri(Paths.get(".").toAbsolutePath().normalize().toString()) + "/";
        }
        LoadingOptions loadingOptions = loadingOptions_;
        if(loadingOptions == null) {
            loadingOptions = new LoadingOptionsBuilder().build();
        }
        return LoaderInstances.${root_loader_name}.documentLoad(doc, baseUri, loadingOptions);
    }

    public static ${root_loader_instance_type} loadDocumentByString(final String doc, final String uri) {
        return loadDocumentByString(doc, uri, null);
    }

    public static ${root_loader_instance_type} loadDocumentByString(final String doc, final String uri, final LoadingOptions loadingOptions_) {
        final Map<String, Object> result = YamlUtils.mapFromString(doc);
        LoadingOptions loadingOptions = loadingOptions_;
        if(loadingOptions == null) {
            loadingOptions = new LoadingOptionsBuilder().setFileUri(uri).build();
        }
        loadingOptions.idx.put(uri, result);
        return LoaderInstances.${root_loader_name}.documentLoad(doc, uri, loadingOptions);
    }

}
