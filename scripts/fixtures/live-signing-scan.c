// Test-only interposition: observe enumeration without changing Security.framework's result.
#include <dirent.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/param.h>
#include <xpc/xpc.h>

static struct dirent *observed_readdir(DIR *directory) {
    char path[MAXPATHLEN];
    const char *watched = getenv("AV_TEST_SCAN_DIRECTORY");
    if (watched && fcntl(dirfd(directory), F_GETPATH, path) == 0 && strcmp(path, watched) == 0) {
        fputs("AV_TEST_DIRECTORY_ENUMERATION\n", stderr);
    }
    return readdir(directory);
}

static xpc_connection_t observed_connection(const char *name, dispatch_queue_t queue) {
    if (name && strcmp(name, "com.apple.CodeSigningHelper") == 0) {
        fputs("AV_TEST_SIGNING_HELPER_LOOKUP\n", stderr);
    }
    return xpc_connection_create(name, queue);
}

__attribute__((used)) static struct {
    const void *replacement;
    const void *original;
} interpose[] __attribute__((section("__DATA,__interpose"))) = {
    { observed_readdir, readdir },
    { observed_connection, xpc_connection_create },
};
