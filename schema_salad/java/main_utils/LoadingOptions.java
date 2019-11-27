package ${package}.utils;

import java.util.Map;
import java.util.HashMap;
import java.util.List;

public class LoadingOptions {
    Fetcher fetcher;
    String fileUri;
    Map<String, String> namespaces;
    List<String> schemas;
    Map<String, Map<String, Object>> idx;
    Map<String, String> vocab;
    Map<String, String> rvocab;

    LoadingOptions(final Fetcher fetcher, final String fileUri, final Map<String, String> namespaces, final List<String> schemas, final Map<String, Map<String, Object>> idx) {
        this.fetcher = fetcher;
        this.fileUri = fileUri;
        this.namespaces = namespaces;
        this.schemas = schemas;
        this.idx = idx;

        if(namespaces != null) {
            this.vocab = (Map<String, String>) ConstantMaps.vocab.clone();
            this.rvocab = (Map<String, String>) ConstantMaps.rvocab.clone();
            for(Map.Entry<String, String> namespaceEntry : namespaces.entrySet()) {
                this.vocab.put(namespaceEntry.getKey(), namespaceEntry.getValue());
                this.rvocab.put(namespaceEntry.getValue(), namespaceEntry.getKey());
            }
        } else {
            this.vocab = (Map<String, String>) ConstantMaps.vocab;
            this.rvocab = (Map<String, String>) ConstantMaps.rvocab;
        }
    }

    public String expandUrl(final String url, final String baseUrl, final boolean scopedId, final boolean vocabTerm, final Integer scopedRef) {
        // NOT CONVERTING this - doesn't match type declaration
        // if not isinstance(url, string_types):
        //    return url
        if(url == "@id" || url == "@type") {
            return url;
        }

        if(vocabTerm && this.vocab.containsKey(url)) {
            return url;
        }
        // TODO... fill out rest.
        return "TODO";
    }



}
