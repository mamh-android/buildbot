#!/bin/sh
#
# ver1.0: 2014-09-09 yfshi@marvell.com bacis function ready

unset GREP_OPTIONS

MSG="$1"
MANY_CATEGORY="Power Performance Stability"

# Check for, and add if missing, a FunctionCategory
#
add_FunctionCategory() {
	clean_message=`sed -e '
		/^diff --git a\/.*/{
			s///
			q
		}
		/^Signed-off-by:/d
		/^#/d
	' "$MSG" | git stripspace`
	if test -z "$clean_message"
	then
		return
	fi

	if test "false" = "`git config --bool --get gerrit.createChangeId`"
	then
		return
	fi

	# Does Change-Id: already exist? if so, exit (no change).
	if grep -i '^Change-Id:' "$MSG" >/dev/null
	then
		return
	fi

	id=`_gen_ChangeId`
	T="$MSG.tmp.$$"
	AWK=awk
	if [ -x /usr/xpg4/bin/awk ]; then
		# Solaris AWK is just too broken
		AWK=/usr/xpg4/bin/awk
	fi

	# How this works:
	# - parse the commit message as (textLine+ blankLine*)*
	# - assume textLine+ to be a footer until proven otherwise
	# - exception: the first block is not footer (as it is the title)
	# - read textLine+ into a variable
	# - then count blankLines
	# - once the next textLine appears, print textLine+ blankLine* as these
	#   aren't footer
	# - in END, the last textLine+ block is available for footer parsing
	$AWK '
	BEGIN {
		# while we start with the assumption that textLine+
		# is a footer, the first block is not.
		isFooter = 0
		footerComment = 0
		blankLines = 0
	}

	# Skip lines starting with "#" without any spaces before it.
	/^#/ { next }

	# Skip the line starting with the diff command and everything after it,
	# up to the end of the file, assuming it is only patch data.
	# If more than one line before the diff was empty, strip all but one.
	/^diff --git a/ {
		blankLines = 0
		while (getline) { }
		next
	}

	# Count blank lines outside footer comments
	/^$/ && (footerComment == 0) {
		blankLines++
		next
	}

	# Catch footer comment
	/^\[[a-zA-Z0-9-]+:/ && (isFooter == 1) {
		footerComment = 1
	}

	/]$/ && (footerComment == 1) {
		footerComment = 2
	}

	# We have a non-blank line after blank lines. Handle this.
	(blankLines > 0) {
		print lines
		for (i = 0; i < blankLines; i++) {
			print ""
		}

		lines = ""
		blankLines = 0
		isFooter = 1
		footerComment = 0
	}

	# Detect that the current block is not the footer
	(footerComment == 0) && (!/^\[?[a-zA-Z0-9-]+:/ || /^[a-zA-Z0-9-]+:\/\//) {
		isFooter = 0
	}

	{
		# We need this information about the current last comment line
		if (footerComment == 2) {
			footerComment = 0
		}
		if (lines != "") {
			lines = lines "\n";
		}
		lines = lines $0
	}

	# Footer handling:
	# If the last block is considered a footer, splice in the Change-Id at the
	# right place.
	# Look for the right place to inject Change-Id by considering
	# CHANGE_ID_AFTER. Keys listed in it (case insensitive) come first,
	# then Change-Id, then everything else (eg. Signed-off-by:).
	#
	# Otherwise just print the last block, a new line and the Change-Id as a
	# block of its own.
	END {
		unprinted = 1
		if (isFooter == 0) {
			print lines "\n"
			lines = ""
		}
		changeIdAfter = "^(" tolower("'"$CHANGE_ID_AFTER"'") "):"
		numlines = split(lines, footer, "\n")
		for (line = 1; line <= numlines; line++) {
			if (unprinted && match(tolower(footer[line]), changeIdAfter) != 1) {
				unprinted = 0
				print "Change-Id: I'"$id"'"
			}
			print footer[line]
		}
		if (unprinted) {
			print "Change-Id: I'"$id"'"
		}
	}' "$MSG" > "$T" && mv "$T" "$MSG" || rm -f "$T"
}
_select_Category() {
    echo "Choose FunctionCategory are:"
    DEFAULT_NUM=1
    while [ -z $MANY_CATEGORY ]; do
            echo -n "Which would you like? ["$DEFAULT_NUM"] "
            if [ -z "$1" ] ; then
                read ANSWER
            else
                echo $1
                ANSWER=$1
            fi
            if echo $ANSWER | egrep -q '^[0-9]+$'; then
                if [ $ANSWER -lt $i ]; then
                    export DEVICE=${device_list[$ANSWER]}
                    echo $DEVICE
                else
                    echo
                    echo "I didn't understand your response.  Please try again."
                    echo
                fi
            elif [ -z $ANSWER ]; then
                export DEVICE=${device_list[$DEFAULT_NUM]}
                echo $DEVICE
            else
                echo
                echo "I didn't understand your response.  Please try again."
                echo
            fi
            if [ -n "$1" ] ; then
                break
            fi
        done

    

}

_select_Category
