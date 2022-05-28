Help()
{
   # Display Help
   echo "Process the data in fused_expand.json and do the mapping"
   echo
   echo "Syntax: start_service.sh [-p|-a|-g|-h]"
   echo "options:"
   echo "h     Show this help panel"
   echo
}

while [ -n "$1" ]; do # while loop starts

	case "$1" in

    -h) Help 
        exit;;

	*) echo "Option $1 not recognized, use option -h to see available options" 
       exit;;

	esac

	shift

done

cd process_artists
python3 map1_artist_id.py
python3 map2_group_id.py
python3 map3_alt_groups.py
python3 map4_same_name.py
python3 map5_member_of.py
python3 map6_composers.py