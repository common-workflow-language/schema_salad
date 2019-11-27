package ${package}.utils;

import java.lang.reflect.Method;
import java.lang.reflect.InvocationTargetException;


public class RecordLoader<T extends Savable> implements Loader<T> {
    private final Class<? extends T> savableClass;

    public RecordLoader(final Class<? extends T> savableClass) {
        this.savableClass = savableClass;
    }

    public T load(final Object doc, final String baseUri, final LoadingOptions loadingOptions, final String docRoot) {
        Loader.validateOfJavaType(java.util.Map.class, doc);
        try {
            final Method method = this.savableClass.getMethod("fromDoc", Object.class, String.class, LoadingOptions.class, String.class);
            T ret = (T) method.invoke(this.savableClass, doc, baseUri, loadingOptions, docRoot);
            if(true) { throw new RuntimeException("loadedRecord" + ret.toString()); }
            return ret;
        } catch(InvocationTargetException e) {
            final Throwable cause = e.getCause();
            if(cause instanceof RuntimeException) {
                throw (RuntimeException) cause;
            }
            throw new RuntimeException(e.getCause());
        } catch(ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }

}