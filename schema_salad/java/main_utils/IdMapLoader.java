package ${package}.utils;


public class IdMapLoader<T> implements Loader<T> {
    private final Loader<T> innerLoader;
    private final String mapSubject;
    private final String mapPredicate;

    public IdMapLoader(final Loader<T> innerLoader, final String mapSubject, final String mapPredicate) {
        this.innerLoader = innerLoader;
        this.mapSubject = mapSubject;
        this.mapPredicate = mapPredicate;
    }

    public T load(final Object doc_, final String baseUri, final LoadingOptions loadingOptions, final String docRoot) {
        Object doc = doc_;
        // TODO: dispatch on map
        return this.innerLoader.load(doc, baseUri, loadingOptions);
    }

}
