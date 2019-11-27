package ${package}.utils;

import java.io.UnsupportedEncodingException;
import java.nio.charset.StandardCharsets;
import java.net.URI;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.net.URISyntaxException;


public class Uris {
    public static String fileUri(final String path) {
        return fileUri(path, false);
    }

    public static String fileUri(final String path, final boolean splitFrag) {
        if(path.equals("file://")) {
            return path;
        }
        String frag;
        String urlPath;
        if(splitFrag) {
            final String[] pathsp = path.split("#", 2);
            // is quoting this?
            urlPath = Uris.quote(pathsp[0]);
            if(pathsp.length == 2) {
                frag = "#" + Uris.quote(pathsp[1]);
            } else {
                frag = "";
                urlPath = Uris.quote(path);
            }
        } else {
            urlPath = Uris.quote(path);
            frag = "";
        }
        if(urlPath.startsWith("//")) {
            return "file:" + urlPath + frag;
        } else {
            return "file://" + urlPath + frag;
        }
    }

    public static URI toUri(final String url) {
        try {
            return new URI(url);
        } catch(URISyntaxException e) {
            throw new RuntimeException(e);
        }
    }


    public static String quote(final String uri) {
        try {
            return java.net.URLDecoder.decode(uri, StandardCharsets.UTF_8.name());
        } catch (UnsupportedEncodingException e) {
            throw new RuntimeException(e);
        }
    }

    public static String unquote(final String uri) {
        try {
            return java.net.URLEncoder.encode(uri, StandardCharsets.UTF_8.name());
        } catch (UnsupportedEncodingException e) {
            throw new RuntimeException(e);
        }
    }

}