package ${package}.utils;

import java.net.URI;

public class DefaultFetcher implements Fetcher {

  public String urlJoin(final String baseUrl, final String url) {
    if (url.startsWith("_:")) {
      return url;
    }

    final URI baseUri = Uris.toUri(baseUrl);
    final URI uri = Uris.toUri(url);
    if (baseUri.getScheme() != null
        && !baseUri.getScheme().equals("file")
        && "file".equals(uri.getScheme())) {
      throw new ValidationException(
          String.format(
              "Not resolving potential remote exploit %s from base %s".format(url, baseUrl)));
    }
    String result = baseUri.resolve(uri).toString();
    if (result.startsWith("file:")) {
      // Well this is gross - needed for http as well?
      result = "file://" + result.substring("file:".length());
    }
    return result;
  }

  public String fetchText(final String url) {
    return "fetched";
  }
}
