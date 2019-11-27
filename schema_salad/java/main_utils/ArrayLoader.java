package ${package}.utils;

import java.util.ArrayList;
import java.util.List;


public class ArrayLoader<T> implements Loader<List<T>> {
    private final Loader<T> itemLoader;

    public ArrayLoader(Loader<T> itemLoader) {
        this.itemLoader = itemLoader;
    }

    public List<T> load(final Object doc, final String baseUri, final LoadingOptions loadingOptions, final String docRoot) {
        if (!(doc instanceof List)) {
            throw new ValidationException("Expected a list");
        }
        final List<Object> docList = (List<Object>) doc;
        final List<T> r = new ArrayList();
        final List<Loader> loaders = new ArrayList<Loader>();
        loaders.add(this);
        loaders.add(this.itemLoader);
        final UnionLoader unionLoader = new UnionLoader(loaders);
        // TODO: validate multiple errors...
        for(final Object el : docList) {
            final Object loadedField = unionLoader.loadField(el, baseUri, loadingOptions);
            if(loadedField instanceof List) {
                r.addAll((List<T>) loadedField);
            } else {
                r.add((T) loadedField);
            }
        }
        return r;
    }

}