package ${package}.utils;

import java.util.ArrayList;
import java.util.List;

public class UriLoader<T> implements Loader<T> {
  private final Loader<T> innerLoader;
  private final boolean scopedId;
  private final boolean vocabTerm;
  private final Integer scopedRef;

  public UriLoader(
      final Loader<T> innerLoader,
      final boolean scopedId,
      final boolean vocabTerm,
      final Integer scopedRef) {
    this.innerLoader = innerLoader;
    this.scopedId = scopedId;
    this.vocabTerm = vocabTerm;
    this.scopedRef = scopedRef;
  }

  private Object expandUrl(
      final Object object, final String baseUri, final LoadingOptions loadingOptions) {
    if (object instanceof String) {
      return loadingOptions.expandUrl(
          (String) object, baseUri, this.scopedId, this.vocabTerm, this.scopedRef);
    } else {
      return object;
    }
  }

  public T load(
      final Object doc_,
      final String baseUri,
      final LoadingOptions loadingOptions,
      final String docRoot) {
    Object doc = doc_;
    if (doc instanceof List) {
      List<Object> docList = (List<Object>) doc;
      List<Object> docWithExpansion = new ArrayList<Object>();
      for (final Object el : docList) {
        docWithExpansion.add(this.expandUrl(el, baseUri, loadingOptions));
      }
      doc = docWithExpansion;
    }
    if (doc instanceof String) {
      doc = this.expandUrl(doc, baseUri, loadingOptions);
    }
    return this.innerLoader.load(doc, baseUri, loadingOptions);
  }
}
