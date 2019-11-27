package ${package}.utils;

import ${package}.utils.ValidationException;


public class PrimitiveLoader<T> implements Loader<T> {
    private Class<T> clazz;

    public PrimitiveLoader(Class<T> clazz) {
        this.clazz = clazz;
    }

    public T load(final Object doc, final String baseUri, final LoadingOptions loadingOptions, final String docRoot) {
        if(!this.clazz.isInstance(doc)) {
            final String message = String.format("Expected a %s but got %s",
                this.clazz.getName(), doc.getClass().getName()
            );
            throw new ValidationException(message);
        }
        return (T) doc;
    }
}
