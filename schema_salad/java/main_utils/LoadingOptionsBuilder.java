package ${package}.utils;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public class LoadingOptionsBuilder {
  private Optional<Fetcher> fetcher = Optional.empty();
  private Optional<String> fileUri = Optional.empty();
  private Optional<Map<String, String>> namespaces = Optional.empty();
  private Optional<List<String>> schemas = Optional.empty();
  private Optional<LoadingOptions> copyFrom = Optional.empty();

  public LoadingOptionsBuilder() {}

  public LoadingOptionsBuilder setFetcher(final Fetcher fetcher) {
    this.fetcher = Optional.of(fetcher);
    return this;
  }

  public LoadingOptionsBuilder copiedFrom(final LoadingOptions copyFrom) {
    this.copyFrom = Optional.of(copyFrom);
    return this;
  }

  public LoadingOptionsBuilder setFileUri(final String fileUri) {
    this.fileUri = Optional.of(fileUri);
    return this;
  }

  public LoadingOptionsBuilder setNamespaces(final Map<String, String> namespaces) {
    this.namespaces = Optional.of(namespaces);
    return this;
  }

  public LoadingOptions build() {
    Fetcher fetcher = this.fetcher.orElse(null);
    String fileUri = this.fileUri.orElse(null);
    List<String> schemas = this.schemas.orElse(null);
    Map<String, String> namespaces = this.namespaces.orElse(null);
    Map<String, Object> idx = new HashMap<String, Object>();
    if (this.copyFrom.isPresent()) {
      final LoadingOptions copyFrom = this.copyFrom.get();
      idx = copyFrom.idx;
      if (fetcher == null) {
        fetcher = copyFrom.fetcher;
      }
      if (fileUri == null) {
        fileUri = copyFrom.fileUri;
      }
      if (namespaces == null) {
        namespaces = copyFrom.namespaces;
        schemas = copyFrom.schemas; // Bug in Python codegen?
      }
    }
    if (fetcher == null) {
      fetcher = new DefaultFetcher();
    }
    return new LoadingOptions(fetcher, fileUri, namespaces, schemas, idx);
  }
}
