package ${package}.utils;

import java.util.ArrayList;
import java.util.List;

public class ArrayLoader<T> implements Loader<List<T>> {
  private final Loader<T> itemLoader;
  private final boolean flatten;

  public ArrayLoader(Loader<T> itemLoader) {
    this(itemLoader, true);
  }

  public ArrayLoader(Loader<T> itemLoader, boolean flatten) {
    this.itemLoader = itemLoader;
    this.flatten = flatten;
  }

  public List<T> load(
      final Object doc,
      final String baseUri,
      final LoadingOptions loadingOptions,
      final String docRoot) {
    final List<Object> docList = (List<Object>) Loader.validateOfJavaType(List.class, doc);
    final List<T> r = new ArrayList();
    final List<Loader> loaders = new ArrayList<Loader>();
    loaders.add(this);
    loaders.add(this.itemLoader);
    final UnionLoader unionLoader = new UnionLoader(loaders);
    final List<ValidationException> errors = new ArrayList();
    for (final Object el : docList) {
      try {
        final Object loadedField = unionLoader.loadField(el, baseUri, loadingOptions);
        if (this.flatten && loadedField instanceof List) {
          r.addAll((List<T>) loadedField);
        } else {
          r.add((T) loadedField);
        }
      } catch (final ValidationException e) {
        errors.add(e);
      }
    }
    if (!errors.isEmpty()) {
      throw new ValidationException("", errors);
    }
    return r;
  }
}
