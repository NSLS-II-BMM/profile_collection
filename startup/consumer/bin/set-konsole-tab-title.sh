# see https://stackoverflow.com/a/54142398
set-konsole-tab-title-type ()
{
    local _title="$1"
    local _type=${2:-0}
    [[ -z "${_title}" ]]               && return 1
    [[ -z "${KONSOLE_DBUS_SERVICE}" ]] && return 1
    [[ -z "${KONSOLE_DBUS_SESSION}" ]] && return 1
    qdbus-qt5 >/dev/null "${KONSOLE_DBUS_SERVICE}" "${KONSOLE_DBUS_SESSION}" setTabTitleFormat "${_type}" "${_title}"
}
set-konsole-tab-title ()
{
    set-konsole-tab-title-type "$1" && set-konsole-tab-title-type "$1" 1
}
command_exists () {
    command -v "$1" >/dev/null 2>&1
}
