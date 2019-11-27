package ${package}.utils;

import java.lang.reflect.Method;


public class RecordLoader<T extends Savable> implements Loader<T> {
    private final Class<T> savableClass;

    public RecordLoader(final Class<T> savableClass) {
        this.savableClass = savableClass;
    }

    public T load(final Object doc, final String baseUri, final LoadingOptions loadingOptions, final String docRoot) {
        if(!(doc instanceof java.util.Map)) {
            throw new ValidationException("Expected a mapping type");
        }
        try {
            final Method method = this.savableClass.getMethod("fromDoc", Object.class, String.class, LoadingOptions.class, String.class);
            return (T) method.invoke(this.savableClass, doc, baseUri, loadingOptions, docRoot);
        } catch(ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }

}