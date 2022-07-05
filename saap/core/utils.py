
class AreaTrabalho():

    def areatrabalho(request):

        if request.user.is_anonymous():
            return {}
        result = {'areatrabalho': [], 'usuario': request.user}
        for at in request.user.operadorareatrabalho_set.all():
            if(at.preferencial == True): 
                result['areatrabalho'].insert(0, {'pk': at.areatrabalho.pk, 'nome': at.areatrabalho.nome})
                request.workspace = at.areatrabalho.pk
            else:
                result['areatrabalho'].append({'pk': at.areatrabalho.pk, 'nome': at.areatrabalho.nome})
        return result
   
