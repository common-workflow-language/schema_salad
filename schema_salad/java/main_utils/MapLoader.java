package ${package}.utils;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class MapLoader<T> implements Loader<Map<String, T>> {
  private final Loader<T> valueLoader;

  public MapLoader(Loader<T> valueLoader) {
    this.valueLoader = valueLoader;
  }

  public Map<String, T> load(
      final Object doc,
      final String baseUri,
      final LoadingOptions loadingOptions,
      final String docRoot) {
    final Map<String, Object> docMap = (Map<String, Object>) Loader.validateOfJavaType(Map.class, doc);
    final Map<String, T> r = new HashMap();
    final List<ValidationException> errors = new ArrayList();
    for (final Map.Entry<String, Object> entry : docMap.entrySet()) {
      try {
        final Object loadedField = this.valueLoader.loadField(entry.getValue(), baseUri, loadingOptions);
        r.put(entry.getKey(), (T) loadedField);
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
