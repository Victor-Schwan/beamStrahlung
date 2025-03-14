# incorporate in $OC/my.env.sh

action() {
    local shell_is_zsh="$( [ -z "${ZSH_VERSION}" ] && echo "false" || echo "true" )"
    local this_file="$( ${shell_is_zsh} && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
    local this_dir="$( cd "$( dirname "${this_file}" )" && pwd )"

    export PYTHONPATH="${this_dir}:${PYTHONPATH}"

    export ANALYSIS_PATH="${codeDir}/beamStrahlung"
    export LAW_HOME=${ANALYSIS_PATH}/.law
    export LAW_CONFIG_FILE=${ANALYSIS_PATH}/law.cfg

    export DATA_PATH="${dtDir}/test_law"
}
action
