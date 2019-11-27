package ${package}.utils;

import java.util.List;


public class UriLoader<T> implements Loader<T> {
    private final Loader<T> innerLoader;
    private final boolean scopedId;
    private final boolean vocabTerm;
    private final Integer scopedRef;

    public UriLoader(final Loader<T> innerLoader, final boolean scopedId, final boolean vocabTerm, final Integer scopedRef) {
        this.innerLoader = innerLoader;
        this.scopedId = scopedId;
        this.vocabTerm = vocabTerm;
        this.scopedRef = scopedRef;
    }

    private Object expandUrl(final Object object, final String baseUri, final LoadingOptions loadingOptions) {
        if(object instanceof String) {
            return loadingOptions.expandUrl(
                (String) object,
                baseUri,
                this.scopedId,
                this.vocabTerm,
                this.scopedRef
            );
        } else {
            return object;
        }
    }

    public T load(final Object doc_, final String baseUri, final LoadingOptions loadingOptions, final String docRoot) {
        Object doc = doc_;
        if(doc instanceof List) {
            List<Object> expandedDoc = (List<Object>) doc;
            for(final Object el : expandedDoc) {
                expandedDoc.add(this.expandUrl(el, baseUri, loadingOptions));
            }
            doc = expandedDoc;
        }
        if(doc instanceof String) {
            doc = this.expandUrl(
                doc,
                baseUri,
                loadingOptions
            );
        }
        return this.innerLoader.load(doc, baseUri, loadingOptions);
    }

}