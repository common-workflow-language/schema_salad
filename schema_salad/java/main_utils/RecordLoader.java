package ${package}.utils;

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;

public class RecordLoader<T extends Saveable> implements Loader<T> {
  private final Class<? extends T> saveableClass;
  private final String container;

  public RecordLoader(final Class<? extends T> saveableClass, final String container) {
    this.saveableClass = saveableClass;
    this.container = container;
  }

  public T load(
      final Object doc,
      final String baseUri,
      final LoadingOptions loadingOptions,
      final String docRoot) {
    Loader.validateOfJavaType(java.util.Map.class, doc);
    try {
      final Constructor<? extends T> constructor =
          this.saveableClass.getConstructor(
              new Class[] {Object.class, String.class, LoadingOptions.class, String.class});
      LoadingOptions innerLoadingOptions = loadingOptions;
      if (this.container != null) {
        innerLoadingOptions = new LoadingOptionsBuilder().copiedFrom(loadingOptions).setContainer(this.container).build();
      }
      final T ret = constructor.newInstance(doc, baseUri, innerLoadingOptions, docRoot);
      return ret;
    } catch (InvocationTargetException e) {
      final Throwable cause = e.getCause();
      if (cause instanceof RuntimeException) {
        throw (RuntimeException) cause;
      }
      throw new RuntimeException(e.getCause());
    } catch (ReflectiveOperationException e) {
      throw new RuntimeException(e);
    }
  }

}
