package ${package}.utils;

import java.util.Arrays;
import java.util.List;


public class EnumLoader implements Loader<String> {
    private final List<String> symbols;

    public EnumLoader(final List<String> symbols) {
        this.symbols = symbols;
    }

    public EnumLoader(final String[] symbols) {
        this(Arrays.asList(symbols));
    }

    public String load(final Object doc, final String baseUri, final LoadingOptions loadingOptions, final String docRoot) {
        if(!(doc instanceof String)) {
            throw new ValidationException("Expected raw string");
        }
        final String docString = (String) doc;
        if(!this.symbols.contains(docString)) {
            throw new ValidationException(String.format("Expected one of %s", this.symbols));
        }
        return docString;
    }

}