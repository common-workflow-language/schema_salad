package ${package}.utils;

import org.junit.Assert;
import org.junit.Test;

public class DefaultFetcherTest {
  @Test
  public void testUnderscoreJoin() {
    final DefaultFetcher fetcher = new DefaultFetcher();
    Assert.assertEquals(fetcher.urlJoin("http://googl.com/", "_:/moo"), "_:/moo");
  }

  /*       

        url = fetcher.urljoin("file:///home/fred/foo.cwl", "../alice/soup.cwl")
        assert url == "file:///home/alice/soup.cwl"
        # relative from root
        url = fetcher.urljoin("file:///home/fred/foo.cwl", "/baz/soup.cwl")
        assert url == "file:///baz/soup.cwl"

        url = fetcher.urljoin(
            "file:///home/fred/foo.cwl", "http://example.com/bar/soup.cwl"
        )
        assert url == "http://example.com/bar/soup.cwl"

        url = fetcher.urljoin("http://example.com/fred/foo.cwl", "soup.cwl")
        assert url == "http://example.com/fred/soup.cwl"

        # Root-relative -- here relative to http host, not file:///
        url = fetcher.urljoin("http://example.com/fred/foo.cwl", "/bar/soup.cwl")
        assert url == "http://example.com/bar/soup.cwl"

        # Security concern - can't resolve file: from http:
        with pytest.raises(ValidationException):
            url = fetcher.urljoin(
                "http://example.com/fred/foo.cwl", "file:///bar/soup.cwl"
            )
  */

  @Test
  public void testUnixJoin() {
    final DefaultFetcher fetcher = new DefaultFetcher();
    String url;

    url = fetcher.urlJoin("file:///home/fred/foo.cwl", "soup.cwl");
    Assert.assertEquals(url, "file:///home/fred/soup.cwl");

    url = fetcher.urlJoin("file:///home/fred/foo.cwl", "../alice/soup.cwl");
    Assert.assertEquals(url, "file:///home/alice/soup.cwl");
    // relative from root
    url = fetcher.urlJoin("file:///home/fred/foo.cwl", "/baz/soup.cwl");
    Assert.assertEquals(url, "file:///baz/soup.cwl");

    url = fetcher.urlJoin("file:///home/fred/foo.cwl", "http://example.com/bar/soup.cwl");
    Assert.assertEquals(url, "http://example.com/bar/soup.cwl");

    url = fetcher.urlJoin("http://example.com/fred/foo.cwl", "soup.cwl");
    Assert.assertEquals(url, "http://example.com/fred/soup.cwl");

    // Root-relative -- here relative to http host, not file:///
    url = fetcher.urlJoin("http://example.com/fred/foo.cwl", "/bar/soup.cwl");
    Assert.assertEquals(url, "http://example.com/bar/soup.cwl");
  }
}
