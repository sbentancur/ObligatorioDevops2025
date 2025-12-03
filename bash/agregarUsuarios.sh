#!/bin/bash

############# Variables 

info_mode=0
set_pwd=0
pwd=""
file=""

############# Validaciones de los parametros ingresados

while  [ $# -gt 0 ];do
	case "$1" in
		-i)
			info_mode=1
			shift
			;;
		-c)
			shift # El sig. parametro debe ser la pwd
			if [ -z "$1" ] || [[ "$1" == -* ]]; then
				echo "############## ERROR ###############" >&2
				echo "La flag -c requiere una contrasenna." >&2
				echo "####################################" >&2
				exit 1 # Si no se ingreso una pwd luego de esta flag se da un error
			fi
			set_pwd=1
			pwd="$1"
			shift
			;;
		-*) # Cualquier otro parametro es incorrecto.
			echo "###### ERROR ######" >&2
			echo "Flag '$1' invalida." >&2
			echo "###################" >&2
                        exit 2
			;;
		*) # Se espera como restante el archivo para la creacion del/los usuario/s
			if [ -z "$file" ];then
				file="$1"
			else # Valida que solo se reciba 1 archivo
				echo "############# ERROR #############" >&2
                        	echo "Cantidad de archivos incorrecta." >&2
                        	echo "#################################" >&2	
				exit 2
			fi
			shift
			;;
	esac
done

############# Validacion de archivo

if [ -z "$file" ];then
	echo "################## ERROR ##################" >&2
	echo "Se debe especificar el archivo de usuarios." >&2
	echo "###########################################" >&2
	exit 3 
fi

if [ ! -e "$file" ];then
	echo "######### ERROR ##########" >&2
	echo "El archivo '$file' no existe." >&2
	echo "##########################" >&2
	exit 4
fi

if [ ! -f "$file" ];then
	echo "########### ERROR ###########" >&2
	echo "'$file' no es un archivo regular" >&2
	echo "#############################" >&2
	exit 5
fi

if [ ! -r "$file" ];then
	echo "######################## ERROR ########################" >&2
	echo "No se tienen permisos de lectura sobre el archivo '$file'." >&2
	echo "#######################################################" >&2
	exit 6
fi

if [ ! -s "$file" ];then
	echo "########## ERROR ##########" >&2
	echo "El archivo '$file' esta vacio." >&2
	echo "###########################" >&2
	exit 7
fi

############# Validaciones formato del archivo

num_linea=0
while IFS= read -r line || [[ -n "$line" ]]; do
	((num_linea++))
	# Si la linea esta vacia en el archivo, continua a la siguiente
	[[ -z "$line" ]] && continue
	
	# Contar los campos de la linea
	campos=$(echo "$line" | awk -F':' '{print NF}')

	if [ $campos -ne 5 ];then
		echo "#################### ERROR ###################" >&2
		echo "La linea $num_linea no tiene exactamente 5 campos." >&2
		echo "##############################################" >&2
		exit 8
	fi
done < "$file"

############# Procesamiento del archivo y creacion de usuarios

creados=0
num_linea=0

while IFS= read -r line; do
    ((num_linea++))

    [[ -z "$line" ]] && continue

    IFS=':' read -r user comm home crear_home shell <<< "$line"

    ### Validación del username
    if  [[ ! "$user" =~ ^[a-zA-Z0-9._-]+$ ]]; then
        echo "########################## ERROR ##########################" >&2
	echo "El nombre de usuario '$user' (linea $num_linea) es invalido." >&2
        echo "###########################################################" >&2
	continue
    fi

    if id "$user" &>/dev/null; then
	echo "######################## ERROR ########################" >&2
        echo "Error: El usuario '$user' ya existe (linea $num_linea)." >&2
        echo "#######################################################" >&2
	continue
    fi

    ### Construcción del useradd
    comando="useradd"

    [[ -n "$comm" ]] && comando="$comando -c \"$comm\""
    [[ -n "$home" ]] && comando="$comando -d \"$home\""
    [[ "$crear_home" == "SI" ]] && comando="$comando -m"
    [[ -n "$shell" ]] && comando="$comando -s \"$shell\""

    comando="$comando $user"

    # Modo informativo
    if [ $info_mode -eq 1 ];then
	    echo "Comando ejecutado: $comando"
    fi

    # Ejecución de useradd
    if eval "$comando"; then
	    if [[ $set_pwd -eq 1 ]]; then
		    if echo "$user:$pwd" | chpasswd;then
			    :
		    else
			    echo "######################## ERROR ########################" >&2
			    echo "No se pudo asignar la contrasenna a "$user"." >&2
			    echo "######################## ERROR ########################" >&2
			    continue
		    fi
            fi

	    if [[ $info_mode -eq 1 ]];then
		    echo "Usuario "$user" creado correctamente."
	    fi
	    creados=$((creados+1))
    else
	    echo "ERROR: Fallo la creacion del usuario '$user' (linea $num_linea)" >&2
	    if [[ $info_mode -eq 1 ]];then
		    echo "Error al crear el usuario '$user'."
	    fi
    fi
done < "$file"

############# Resumen final modo info
if [[ $info_mode -eq 1 ]];then
	echo ""
	echo "---------------------"
	echo "Usuarios creados: $creados"
	echo "---------------------"
fi
