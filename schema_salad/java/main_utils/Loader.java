package ${package}.utils;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.yaml.snakeyaml.Yaml;

public interface Loader {

    abstract Object load(final Object doc, final String baseUri, final LoadingOptions loadingOptions, final String docRoot);

    default Object load(final Object doc, final String baseUri, final LoadingOptions loadingOptions) {
        return load(doc, baseUri, loadingOptions, null);
    }

    default Object documentLoad(final String doc, final String baseUri, final LoadingOptions loadingOptions) {
        return load(doc, baseUri, loadingOptions);
    }

    default Object documentLoad(final Map<String, Object> doc_, final String baseUri_, final LoadingOptions loadingOptions_) {
        Map<String, Object> doc = doc_;
        LoadingOptions loadingOptions = loadingOptions_;
        if(doc.containsKey("$namespaces")) {
            final Map<String, String> namespaces = (Map<String, String>) doc.get("$namespaces");
            loadingOptions = new LoadingOptionsBuilder().copiedFrom(loadingOptions).setNamespaces(namespaces).build();
            doc = copyWithoutKey(doc, "$namespaces");
        }
        /*
        if "$namespaces" in doc:
            loadingOptions = LoadingOptions(
                copyfrom=loadingOptions, namespaces=doc["$namespaces"]
            )
            doc = {k: v for k, v in doc.items() if k != "$namespaces"}

        if "$schemas" in doc:
            loadingOptions = LoadingOptions(
                copyfrom=loadingOptions, schemas=doc["$schemas"]
            )
            doc = {k: v for k, v in doc.items() if k != "$schemas"}
        */
        String baseUri = baseUri_;
        if(doc.containsKey("$base")) {
            baseUri = (String) doc.get("$base");
        }
        if(doc.containsKey("$graph")) {
            return load(doc.get("$graph"), baseUri, loadingOptions);
        } else {
            return load(doc, baseUri, loadingOptions, baseUri);
        }
    }

    default Object documentLoad(final List<Object> doc, final String baseUri, final LoadingOptions loadingOptions) {
        return load(doc, baseUri, loadingOptions);
    }

    default Object documentLoadByUrl(final String url, final LoadingOptions loadingOptions) {
        if(loadingOptions.idx.containsKey(url)) {
            return documentLoad(loadingOptions.idx.get(url), url, loadingOptions);
        }

        final String text = loadingOptions.fetcher.fetchText(url);
        Yaml yaml = new Yaml();
        final Map<String, Object> result = yaml.load(text);
        loadingOptions.idx.put(url, result);
        final LoadingOptionsBuilder urlLoadingOptions = new LoadingOptionsBuilder().copiedFrom(loadingOptions).setFileUri(url);
        return documentLoad(result, url, urlLoadingOptions.build());
    }

    private Map<String, Object> copyWithoutKey(final Map<String, Object> doc, final String key) {
        final Map<String, Object> result = new HashMap();
        for(final Map.Entry<String, Object> entry : doc.entrySet()) {
            if(entry.getKey() != key) {
                result.put(entry.getKey(), entry.getValue());
            }
        }
        return result;
    }

}