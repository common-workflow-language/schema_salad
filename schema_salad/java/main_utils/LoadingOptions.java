package ${package}.utils;

import java.net.URI;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

public class LoadingOptions {
  Fetcher fetcher;
  String fileUri;
  Map<String, String> namespaces;
  List<String> schemas;
  Map<String, Map<String, Object>> idx;
  Map<String, String> vocab;
  Map<String, String> rvocab;

  LoadingOptions(
      final Fetcher fetcher,
      final String fileUri,
      final Map<String, String> namespaces,
      final List<String> schemas,
      final Map<String, Map<String, Object>> idx) {
    this.fetcher = fetcher;
    this.fileUri = fileUri;
    this.namespaces = namespaces;
    this.schemas = schemas;
    this.idx = idx;

    if (namespaces != null) {
      this.vocab = (Map<String, String>) ConstantMaps.vocab.clone();
      this.rvocab = (Map<String, String>) ConstantMaps.rvocab.clone();
      for (Map.Entry<String, String> namespaceEntry : namespaces.entrySet()) {
        this.vocab.put(namespaceEntry.getKey(), namespaceEntry.getValue());
        this.rvocab.put(namespaceEntry.getValue(), namespaceEntry.getKey());
      }
    } else {
      this.vocab = (Map<String, String>) ConstantMaps.vocab;
      this.rvocab = (Map<String, String>) ConstantMaps.rvocab;
    }
  }

  public String expandUrl(
      String url_,
      final String baseUrl,
      final boolean scopedId,
      final boolean vocabTerm,
      final Integer scopedRef) {
    // NOT CONVERTING this - doesn't match type declaration
    // if not isinstance(url, string_types):
    //    return url
    String url = url_;
    if (url.equals("@id") || url.equals("@type")) {
      return url;
    }

    if (vocabTerm && this.vocab.containsKey(url)) {
      return url;
    }

    if (!this.vocab.isEmpty() && url.contains(":")) {
      String prefix = url.split(":", 1)[0];
      if (this.vocab.containsKey(prefix)) {
        url = this.vocab.get(prefix) + url.substring(prefix.length() + 1);
      }
    }

    URI split = Uris.toUri(url);
    final String scheme = split.getScheme();
    final boolean hasFragment = stringHasContent(split.getFragment());
    if (scheme != null
        && ((scheme.length() > 0
                && (scheme.equals("http") || scheme.equals("https") || scheme.equals("file")))
            || url.startsWith("$(")
            || url.startsWith("${"))) {
      // pass
    } else if (scopedId && !hasFragment) {
      final URI splitbase = Uris.toUri(baseUrl);
      final String frg;
      if (stringHasContent(splitbase.getFragment())) {
        frg = splitbase.getFragment() + "/" + split.getPath();
      } else {
        frg = split.getPath();
      }
      String pt;
      if (!splitbase.getPath().equals("")) {
        pt = splitbase.getPath();
      } else {
        pt = "/";
      }
      try {
        url =
            new URI(splitbase.getScheme(), splitbase.getAuthority(), pt, splitbase.getQuery(), frg)
                .toString();
      } catch (java.net.URISyntaxException e) {
        throw new RuntimeException(e);
      }
    } else if (scopedRef != null && !hasFragment) {
      final URI splitbase = Uris.toUri(baseUrl);
      final ArrayList<String> sp = new ArrayList(Arrays.asList(splitbase.getFragment().split("/")));
      int n = scopedRef;
      while (n > 0 && sp.size() > 0) {
        sp.remove(0);
        n -= 1;
      }
      sp.add(url);
      final String fragment = String.join("/", sp);
      try {
        url =
            new URI(
                    splitbase.getScheme(),
                    splitbase.getAuthority(),
                    splitbase.getPath(),
                    splitbase.getQuery(),
                    fragment)
                .toString();
      } catch (java.net.URISyntaxException e) {
        throw new RuntimeException(e);
      }
    } else {
      url = this.fetcher.urlJoin(baseUrl, url);
    }

    if (vocabTerm) {
      split = Uris.toUri(url);
      if (stringHasContent(split.getScheme())) {
        if (this.rvocab.containsKey(url)) {
          return this.rvocab.get(url);
        }
      } else {
        throw new ValidationException("Term '{}' not in vocabulary".format(url));
      }
    }
    return url;
  }

  static boolean stringHasContent(final String s) {
    return s != null && s.length() > 0;
  }
}
