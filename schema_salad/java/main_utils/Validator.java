package ${package}.utils;

import java.io.File;

public class Validator {
    public static void main(final String[] args) throws Exception {
        if(args.length != 1) {
            throw new Exception("No argument supplied to validate.");
        }
        // TODO: allow URLs and such.
        final File uri = new File(args[0]);
        RootLoader.loadDocument(uri);
    }
}
