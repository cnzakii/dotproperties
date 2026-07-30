import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.Properties;

/**
 * Reference compiled and run on every JDK in the interoperability matrix.
 * The source remains compatible with Java 8.
 */
public final class JavaPropertiesReference {
    private JavaPropertiesReference() {}

    public static void main(String[] args) throws Exception {
        if (args.length == 1 && "version".equals(args[0])) {
            System.out.println(System.getProperty("java.specification.version"));
            return;
        }
        if (args.length == 2 && "load-bytes".equals(args[0])) {
            loadBytes(Paths.get(args[1]));
            return;
        }
        if (args.length == 2 && "load-reader".equals(args[0])) {
            loadReader(Paths.get(args[1]));
            return;
        }
        if (args.length == 3 && "store-bytes".equals(args[0])) {
            storeBytes(Paths.get(args[1]), Paths.get(args[2]));
            return;
        }
        if (args.length == 3 && "store-writer".equals(args[0])) {
            storeWriter(Paths.get(args[1]), Paths.get(args[2]));
            return;
        }
        throw new IllegalArgumentException("invalid reference arguments");
    }

    private static void loadBytes(Path source) throws Exception {
        Properties properties = new Properties();
        try (InputStream input = new FileInputStream(source.toFile())) {
            properties.load(input);
        }
        printProperties(properties);
    }

    private static void loadReader(Path source) throws Exception {
        Properties properties = new Properties();
        try (Reader reader =
                new InputStreamReader(
                        new FileInputStream(source.toFile()), StandardCharsets.UTF_8)) {
            properties.load(reader);
        }
        printProperties(properties);
    }

    private static void storeBytes(Path mapping, Path destination) throws Exception {
        Properties properties = readMapping(mapping);
        try (OutputStream output = new FileOutputStream(destination.toFile())) {
            properties.store(output, null);
        }
    }

    private static void storeWriter(Path mapping, Path destination) throws Exception {
        Properties properties = readMapping(mapping);
        try (Writer writer =
                new OutputStreamWriter(
                        new FileOutputStream(destination.toFile()), StandardCharsets.UTF_8)) {
            properties.store(writer, null);
        }
    }

    private static Properties readMapping(Path source) throws Exception {
        Properties properties = new Properties();
        try (BufferedReader reader = Files.newBufferedReader(source, StandardCharsets.US_ASCII)) {
            String line;
            while ((line = reader.readLine()) != null) {
                int separator = line.indexOf('\t');
                if (separator < 0) {
                    throw new IllegalArgumentException("invalid mapping line");
                }
                properties.setProperty(
                        decode(line.substring(0, separator)),
                        decode(line.substring(separator + 1)));
            }
        }
        return properties;
    }

    private static void printProperties(Properties properties) throws Exception {
        List<String> keys = new ArrayList<String>(properties.stringPropertyNames());
        Collections.sort(keys);
        BufferedWriter writer =
                new BufferedWriter(
                        new OutputStreamWriter(System.out, StandardCharsets.US_ASCII));
        for (String key : keys) {
            writer.write(encode(key));
            writer.write('\t');
            writer.write(encode(properties.getProperty(key)));
            writer.newLine();
        }
        writer.flush();
    }

    private static String encode(String value) {
        StringBuilder encoded = new StringBuilder(value.length() * 4);
        for (int index = 0; index < value.length(); index++) {
            String unit =
                    Integer.toHexString(value.charAt(index)).toUpperCase(Locale.ROOT);
            for (int padding = unit.length(); padding < 4; padding++) {
                encoded.append('0');
            }
            encoded.append(unit);
        }
        return encoded.toString();
    }

    private static String decode(String encoded) {
        if (encoded.length() % 4 != 0) {
            throw new IllegalArgumentException("invalid UTF-16 unit sequence");
        }
        StringBuilder value = new StringBuilder(encoded.length() / 4);
        for (int index = 0; index < encoded.length(); index += 4) {
            value.append((char) Integer.parseInt(encoded.substring(index, index + 4), 16));
        }
        return value.toString();
    }
}
