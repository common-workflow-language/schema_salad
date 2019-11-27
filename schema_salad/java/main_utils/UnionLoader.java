package ${package}.utils;

import java.util.List;
import java.util.Arrays;


public class UnionLoader implements Loader<Object> {
    private final List<Loader> alternates;

    public UnionLoader(List<Loader> alternates) {
        this.alternates = alternates;
    }

    public UnionLoader(Loader[] alternates) {
        this(Arrays.asList(alternates));
    }

    public Object load(final Object doc, final String baseUri, final LoadingOptions loadingOptions, final String docRoot) {
        // TODO: catch validation exceptions and format pretty error.
        for(final Loader loader : this.alternates) {
            try {
                return loader.load(doc, baseUri, loadingOptions, docRoot);
            } catch(ValidationException e) {
                // pass
            }
        }
        throw new ValidationException("Failed to match union type");
    }
}
