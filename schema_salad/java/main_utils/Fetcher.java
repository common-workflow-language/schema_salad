package ${package}.utils;

import java.net.URLDecoder;
import java.net.URLEncoder;


public interface Fetcher {

    public abstract String urlJoin(final String baseUrl, final String url);

    public abstract String fetchText(final String url);

}
