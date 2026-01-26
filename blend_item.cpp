#include "stdafx.h"
#include "constants.h"
#include "log.h"
#include "locale_service.h"
#include "item.h"
#include "blend_item.h"

#define DO_ALL_BLEND_INFO(iter)	for (iter=s_blend_info.begin(); iter!=s_blend_info.end(); ++iter)
#define DO_ALL_ECS_BONUS(iter)	for (iter=s_ecs_bonus_info.begin(); iter!=s_ecs_bonus_info.end(); ++iter)

struct BLEND_ITEM_INFO
{
	DWORD	item_vnum;
	int		apply_type;
	int		apply_value[MAX_BLEND_ITEM_VALUE];
	int		apply_duration[MAX_BLEND_ITEM_VALUE];
};

// Energy Crystal (51002) bonus structure
struct ECS_BONUS_INFO
{
	int		bonus_index;
	int		apply_type;
	int		apply_value;
	int		apply_duration;
};

typedef std::vector<BLEND_ITEM_INFO*>	T_BLEND_ITEM_INFO;
typedef std::vector<ECS_BONUS_INFO*>	T_ECS_BONUS_INFO;

T_BLEND_ITEM_INFO	s_blend_info;
T_ECS_BONUS_INFO	s_ecs_bonus_info;

bool	Blend_Item_init()
{
	BLEND_ITEM_INFO	*blend_item_info = NULL;
	ECS_BONUS_INFO	*ecs_bonus_info = NULL;
	T_BLEND_ITEM_INFO::iterator			iter;
	T_ECS_BONUS_INFO::iterator			ecs_iter;
	char	file_name[256];
	snprintf (file_name, sizeof(file_name), "%s/blend.txt", LocaleService_GetBasePath().c_str());

	sys_log(0, "Blend_Item_init %s ", file_name);

	DO_ALL_BLEND_INFO(iter)
	{
		blend_item_info = *iter;
		M2_DELETE(blend_item_info);
	}
	s_blend_info.clear();

	DO_ALL_ECS_BONUS(ecs_iter)
	{
		ecs_bonus_info = *ecs_iter;
		M2_DELETE(ecs_bonus_info);
	}
	s_ecs_bonus_info.clear();

	if (false==Blend_Item_load(file_name))
	{
		sys_err("<Blend_Item_init> fail");
		return false;
	}
	return true;
}

bool	Blend_Item_load(char *file)
{
	FILE	*fp;
	char	one_line[256];
	const char	*delim = " \t\r\n";
	char	*v;

	BLEND_ITEM_INFO	*blend_item_info{};
	ECS_BONUS_INFO	*ecs_bonus_info{};
	bool	is_ecs_section = false;

	if (0==file || 0==file[0])
		return false;

	if ((fp = fopen(file, "r"))==0)
		return false;

	while (fgets(one_line, 256, fp))
	{
		if (one_line[0]=='#')
			continue;

		const char* token_string = strtok(one_line, delim);

		if (NULL==token_string)
			continue;

		TOKEN("section")
		{
			blend_item_info = M2_NEW BLEND_ITEM_INFO;
			memset(blend_item_info, 0x00, sizeof(BLEND_ITEM_INFO));
			is_ecs_section = false;
		}
		else TOKEN("energy_crystal_bonus")
		{
			ecs_bonus_info = M2_NEW ECS_BONUS_INFO;
			memset(ecs_bonus_info, 0x00, sizeof(ECS_BONUS_INFO));
			is_ecs_section = true;
		}
		else TOKEN("bonus_index")
		{
			v = strtok(NULL, delim);

			if (NULL==v)
			{
				fclose(fp);
				return false;
			}

			str_to_number(ecs_bonus_info->bonus_index, v);
		}
		else TOKEN("item_vnum")
		{
			v = strtok(NULL, delim);

			if (NULL==v)
			{
				fclose(fp);
				return false;
			}

			str_to_number(blend_item_info->item_vnum, v);
		}
		else TOKEN("apply_type")
		{
			v = strtok(NULL, delim);

			if (NULL==v)
			{
				fclose(fp);
				return false;
			}

			if (is_ecs_section)
				ecs_bonus_info->apply_type = FN_get_apply_type(v);
			else
				blend_item_info->apply_type = FN_get_apply_type(v);
		}
		else TOKEN("apply_value")
		{
			if (is_ecs_section)
			{
				v = strtok(NULL, delim);

				if (NULL==v)
				{
					fclose(fp);
					return false;
				}

				str_to_number(ecs_bonus_info->apply_value, v);
			}
			else
			{
				for (int i=0; i<MAX_BLEND_ITEM_VALUE; ++i)
				{
					v = strtok(NULL, delim);

					if (NULL==v)
					{
						fclose(fp);
						return false;
					}

					str_to_number(blend_item_info->apply_value[i], v);
				}
			}
		}
		else TOKEN("apply_duration")
		{
			if (is_ecs_section)
			{
				v = strtok(NULL, delim);

				if (NULL==v)
				{
					fclose(fp);
					return false;
				}

				str_to_number(ecs_bonus_info->apply_duration, v);
			}
			else
			{
				for (int i=0; i<MAX_BLEND_ITEM_VALUE; ++i)
				{
					v = strtok(NULL, delim);

					if (NULL==v)
					{
						fclose(fp);
						return false;
					}

					str_to_number(blend_item_info->apply_duration[i], v);
				}
			}
		}
		else TOKEN("end")
		{
			if (is_ecs_section)
			{
				s_ecs_bonus_info.emplace_back(ecs_bonus_info);
				sys_log(0, "ECS Bonus loaded: index %d, type %d, value %d, duration %d",
					ecs_bonus_info->bonus_index, ecs_bonus_info->apply_type,
					ecs_bonus_info->apply_value, ecs_bonus_info->apply_duration);
			}
			else
			{
				s_blend_info.emplace_back(blend_item_info);
			}
		}
	}

	fclose(fp);

	sys_log(0, "Blend_Item_load: Loaded %d blend items, %d ECS bonuses",
		s_blend_info.size(), s_ecs_bonus_info.size());

	return true;
}

static int FN_random_index()
{
	int	percent = number(1,100);

	if (percent<=10)			// level 1 :10%
		return 0;
	else if (percent<=30)		// level 2 : 20%
		return 1;
	else if (percent<=70)		// level 3 : 40%
		return 2;
	else if (percent<=90)		// level 4 : 20%
		return 3;
	else
		return 4;				// level 5 : 10%

	return 0;
}

// Select random bonus from Energy Crystal bonus pool
static ECS_BONUS_INFO* FN_ECS_select_random_bonus()
{
	if (s_ecs_bonus_info.empty())
		return NULL;

	int random_index = number(0, s_ecs_bonus_info.size() - 1);
	return s_ecs_bonus_info[random_index];
}

bool	Blend_Item_set_value(LPITEM item)
{
	// Handle Energy Crystal (51002) - select random bonus from pool
	if (item->GetVnum() == 51002)
	{
		ECS_BONUS_INFO* selected_bonus = FN_ECS_select_random_bonus();

		if (selected_bonus == NULL)
		{
			sys_err("ECS: No bonus available for item 51002");
			return false;
		}

		sys_log(0, "ECS: Selected bonus index %d, type %d, value %d, duration %d",
			selected_bonus->bonus_index, selected_bonus->apply_type,
			selected_bonus->apply_value, selected_bonus->apply_duration);

		item->SetSocket(0, selected_bonus->apply_type);
		item->SetSocket(1, selected_bonus->apply_value);
		item->SetSocket(2, selected_bonus->apply_duration);
		return true;
	}

	// Handle regular blend items
	BLEND_ITEM_INFO	*blend_info;
	T_BLEND_ITEM_INFO::iterator	iter;

	DO_ALL_BLEND_INFO(iter)
	{
		blend_info = *iter;
		if (blend_info->item_vnum == item->GetVnum())
		{
			int	apply_type;
			int	apply_value;
			int	apply_duration;

			apply_type		= blend_info->apply_type;
			apply_value		= blend_info->apply_value		[FN_random_index()];
			apply_duration	= blend_info->apply_duration	[FN_random_index()];

			sys_log (0, "blend_item : type : %d, value : %d, du : %d", apply_type, apply_value, apply_duration);
			item->SetSocket(0, apply_type);
			item->SetSocket(1, apply_value);
			item->SetSocket(2, apply_duration);
			return true;
		}

	}
	return false;
}

bool	Blend_Item_find(DWORD item_vnum)
{
	// Energy Crystal is always a valid blend item
	if (item_vnum == 51002)
		return true;

	BLEND_ITEM_INFO	*blend_info;
	T_BLEND_ITEM_INFO::iterator	iter;

	DO_ALL_BLEND_INFO(iter)
	{
		blend_info = *iter;
		if (blend_info->item_vnum == item_vnum)
			return true;
	}
	return false;
}
