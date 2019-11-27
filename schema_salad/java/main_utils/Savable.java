package ${package}.utils;


public interface Savable {
    
    public static Object fromDoc(Object doc, String baseUri, LoadingOptions loadingOptions, String docRoot) {
        // subclasses should override. I guess this should be a constructor?
        return null;
    }

    public abstract void save(boolean top, String baseUrl, boolean relativeUris);

}
