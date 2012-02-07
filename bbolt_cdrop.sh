#!/bin/sh
# 

help() {
    if [ -n "$1" ]; then
	echo "Error: $1"
	echo
    fi
    echo "Usage: bbolt_cdrop.sh -i <path> -o <path> -l <list>"
    echo
    echo "bbolt_cdrop is used by buildbolt to publish the prebuilt binaries"
    echo " and source code for code drop."
    echo
    echo "List format:"
    echo "<source> [:space:] <destination>"
    echo "  Don't include any spaces in either <source> or <destination>"
    echo
    exit 0
}

IDIR=
ODIR=
LIST=

validate_parameters() {
    if [ $# -ne 6 ]; then
	help
    fi

    while [ $# -gt 0 ];
    do
	case "$1" in
	    "-i")
		IDIR=$2
		;;
	    "-o")
		ODIR=$2
		;;
	    "-l")
		LIST=$2
		;;
	    *)
		help "Here is an unknown option: $1."
		;;
	esac
	shift 2
    done

    if [ -z "$IDIR" -o ! -d "$IDIR" ]; then
	help "Please specify a valid input directory!"
    fi
    if [ -z "$ODIR" -o ! -d "$ODIR" ]; then
	help "Please specify a valid output directory!"
    fi
    if [ -z "$LIST" -o ! -f "$LIST" ]; then
	help "Please specify a valid list file!"
    fi
}

parse_copy_list() {

CDROP_COPY_PATTERN="
    {
        if (NF < 2 || \$2 == \"\")
            \$2 = \$1;
        system(\"cp -f \"idir\"/\"\$1\" \"odir\"/\"\$2);
    }
"

    awk -v idir="$1" -v odir="$2" "$CDROP_COPY_PATTERN" $3
}

validate_parameters $*
parse_copy_list "$IDIR" "$ODIR" "$LIST"
