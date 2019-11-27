package ${package}.utils;


public class TypeDslLoader<T> implements Loader<T> {
    private final Loader<T> innerLoader;
    private final Integer refScope;

    public TypeDslLoader(final Loader<T> innerLoader, final Integer refScope) {
        this.innerLoader = innerLoader;
        this.refScope = refScope;
    }

    public T load(final Object doc_, final String baseUri, final LoadingOptions loadingOptions, final String docRoot) {
        // TODO: dispatch on String and List
        Object doc = doc_;
        return this.innerLoader.load(doc, baseUri, loadingOptions);
    }

}