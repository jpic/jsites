/*global $ */

/*
Set up a change_form template in: /templates/admin/YOURAPP/YOURMODEL/change_form.html
    
    {% extends "admin/templates/admin/change_form.html" %}
    {% load i18n admin_modify adminmedia %}
    
    {% block extrahead %}{{ block.super }}
    <script type="text/javascript" src="/static/jquery.min.js"></script>
    <script type="text/javascript" src="/media/js/urlify.js"></script>
    <!-- Sorry, you need this one, i might get rid of it later -->
    <script type="text/javascript" src="/static/js/php.min.js"></script>

    <script>
    $(document).ready(function() {
    // Load the javascript snippet here because it parses the HTML
    $.getScript('/static/js/jpic.js', function() {
        
        // Select a "tab" to focus on
        jpicTabManager.select('fieldset_id');

        // There you can play with ui
    })});
    </script>
    {% endblock %}

Example UI playing:
ChampsPourLotSansResidenceSeulement = new Array(
    'departement',
    'cp',
    'ville',
    'addresse1',
    'addresse2',
    'secteur',
    'quartier',
    'ville_diffusion',
    'gps'
);

ChampsPourLocationSeulement = new Array(
    'estimation_cc',
    'loyer_hc', 
    'prov_charges', 
    'loyer_cc', 
    'garantie', 
    'dg_telecommande', 
    'taux_honoraires_locataire', 
    'taux_honoraires_proprietaire', 
    'honoraires_locataire', 
    'honoraires_proprietaire', 
    'frais_dossier', 
    'part_locataire', 
    'part_proprietaire', 
    'numero_clef',
    'assurance',
    'loyer_impayes', 
    'premiere_occupation', 
    'premiere_occupation_duree', 
    'vacance_locative', 
    'vacance_locative_duree',
    'taux_assurance',
    'centre_des_impots',
    'compagnie_des_eaux',
    'bail',
    'Compteur',
    'Locations',
    'Meubles',
    'Charges'
);
ChampsPourVenteSeulement = new Array(
    'droits',
    'loi_defisc',
    'actabilite',
    'estimation', 
    'prix_net_vendeur', 
    'honoraires', 
    'taux_ttc', 
    'alachargede', 
    'prix_fai', 
    'frais_notaire_reduit', 
    'base_honoraires_commercial', 
    'notaire_vendeur',
    'notaire',
    'gestionnaire_existe',
    'gestionnaire'
);

$(document).ready(function() {
    $.getScript('/static/js/jpic.js', function() {

    ui.addConstraint('loi_defisc', 'droits', 'A', jpicFieldValueNotEqual);
    ui.addConstraint(
        ChampsPourLocationSeulement,
        'vente_location',
        'Location',
        jpicFieldValueEqual
    );
    ui.addConstraint(
        ChampsPourVenteSeulement,
        'vente_location',
        'Vente',
        jpicFieldValueEqual
    );
    ui.addConstraint(
        ChampsPourLotSansResidenceSeulement,
        'residence', 
        '',
        jpicFieldValueEqual
    );

    ui.addConstraint([
            'actabilite',
            'livraison_prevue',
            'livraison_prevue_le',
            'livraison_realisee_le',
        ],
        'genre',
        'Neuf',
        jpicFieldValueEqual
    );

    ui.addConstraint([
            'chambres',
            'etages',
        ],
        'sous_type',
        [
            'chambre',
            'garage',
        ],
        jpicFieldValueNotLike
    );

    function maj()
    {
        ui.update();

        var sous_type = new jpicField('sous_type').getValue();
        if (sous_type && sous_type.indexOf('Chambre') >= 0)
        {
            $('#id_type_taille').val('1');
        }

        var label = "";
        if ($('#id_vente_location').val() == 'Location')
        {
            label = "Clause particulières au bail";
        }
        else
        {
            label = "Bloc notes";
        }
        $('label[for=id_bloc_notes]').html(label+":")
    }
    $('#id_sous_type').change(maj);
    $('#id_residence').change(maj);
    $('#id_vente_location').change(maj);
    $('#id_droits').change(maj);
    $('#id_genre').change(maj);
    maj();
    jpicTabManager.select('id_mandat');
    });
});

*/

// window.loadFirebugConsole();

// conditions pattern
function assert() {
    var report = '';
    for (var i=0; i < this.conditions.length; i++)
    {
        if (!this.conditions[i].assert())
        {
            return false;
        }
        report += ', '+this.conditions[i].verbose;
    }
    
    //console.log(this.conditions.length + ' assertions verified OK for field '+this.name+report);
    return true;
};

// {{{ field "class"
var jpicField = function(name) {
    this.name = name;
    this.id = 'id_' + name;
    this.conditions = [];
    this.element = $('#' + this.id);
    this.container = this.element.parent();
    this.row = this.container.parent();
    this.label = $('label[for='+this.id+']');
};
jpicField.prototype.assert = assert;
jpicField.prototype.getValue = function() {
    // support for autocomplete snippets
    if ($('#lookup_'+this.name).length)
    {
        return $('#lookup_'+this.name).val();
    }

    if ($('#' + this.id + '[type=select]').length)
    {
        var text = $('#' + this.id).children(':selected').text();
        if ($('#' + this.id).val())
        {
            this.value = text;
        }
        else
        {
            this.value = false;
        }
        return this.value;
    }

    if ($('#' + this.id).length)
    {
        this.value = $('#' + this.id).val();
    }
    else
    {
        console.error('Cannot find value for ' + this.id);
    }

    return this.value;
};
jpicField.prototype.show = function() {
    this.container.show();

    var showRow = true;
    
    // Don't show the row if any field box is still visible
    this.row.find('div.field-box:visible').each(function() {
        showRow = false;
    });

    // Because finding div.field-box:visible sometimes finds field-box as
    // visible even though they are in a hidden row with 
    // Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.0.6) Gecko/2009030910 Gentoo Firefox/3.0.6
    // Which will be imposed.
    if (!this.row.is(":visible")) {
        showRow = true;
    }

    if (showRow)
    {
        this.row.show();
    }
};
jpicField.prototype.hide = function() {
    this.container.hide();

    var hideRow = true;
    this.row.find('div.field-box').each(function() {
        if($(this).is(":visible"))
        {
            hideRow = false;
        }
    });

    if (hideRow)
    {
        this.row.hide();
    }
};

var jpicMapField = function(name) {
    this.name = name;
    this.id = 'id_' + name;
    this.conditions = [];
};
jpicMapField.prototype.assert = assert;
jpicMapField.prototype.hide = function() {
    $('#' + this.id).parent().hide();
    $('label[for=' + this.id + ']').hide();
    $('#id_' + this.name + '_admin_map').hide();
};
jpicMapField.prototype.show = function() {
    $('#' + this.id).parent().show();
    $('label[for=' + this.id + ']').show();
    $('#id_' + this.name + '_admin_map').show();
};
// }}}
// {{{ fieldset/tab
var jpicDjangoAdmin = function(name, error, id) {
    this.name = name;
    this.error = error;
    if (id == undefined)
    {
        this.id = 'id_' + URLify(this.name, 253);
    }
    else
    {
        this.id = id;
    }
    this.element = null;
};
jpicDjangoAdmin.factory = function(element, name) {
    if (name == undefined)
    {
        var name = element.find("h2").html();
    }

    if (!name)
    {
        //alert("could not create jpicDjangoAdmin object, missing name");
        return false;
    }

    var error = element.find('.errorlist').html();

    var fieldset = new jpicDjangoAdmin(name, error);
    fieldset.element = element;
    element.addClass(fieldset.id);

    return fieldset;
};
jpicDjangoAdmin.prototype.getTab = function() {
    if(this.tab === undefined)
    {
        this.tab = new jpicTab(this.name, this.error);
    }
    return this.tab;
};
// TODO: refactor hide/show
jpicDjangoAdmin.prototype.show = function() {
    if (this.stacked)
    {
        thisname = this.name
        $('div.inline-group').each(function() {
            var name = $(this).find("h2").html();
            //console.log("testing '"+name+"' against '"+this.name+"'");
            if (name == thisname)
            {
                $(this).show();
            }
        });
    }
    else
    {
        if($('fieldset.'+this.id).parent().hasClass('tabular'))
        {
            $('fieldset.'+this.id).parent().parent().show();
        }
        else
        {
            $('fieldset.'+this.id).show();
        }
    }
};
jpicDjangoAdmin.prototype.hide = function() {
    if (this.stacked)
    {
        thisname = this.name
        $('div.inline-group').each(function() {
            var name = $(this).find("h2").html();
            //console.log("testing '"+name+"' against '"+this.name+"'");
            if (name == thisname)
            {
                $(this).hide();
            }
        });
    }
    else
    {
        if($('fieldset.'+this.id).parent().hasClass('tabular'))
        {
            $('fieldset.'+this.id).parent().parent().hide();
        }
        else
        {
            $('fieldset.'+this.id).hide();
        }
    }
};

var jpicDivTab = function(name, error, id) {
    this.name = name;
    this.error = error;
    if (id == undefined)
    {
        this.id = 'id_' + URLify(this.name, 253);
    }
    else
    {
        this.id = id;
    }
    this.element = null;
};
jpicDivTab.factory = function(element) {
    var name = element.find("h1").html();

    if (!name)
    {
        name = element.find("h2").html();
        if (!name)
        {
            return false;
        }
    }

    var error = element.find('.errorlist').html();

    var divtab = new jpicDivTab(name, error);
    divtab.element = element;
    element.addClass(divtab.id);
    return divtab;
};
jpicDivTab.prototype.getTab = function() {
    if(this.tab === undefined)
    {
        this.tab = new jpicTab(this.name, this.error);
    }
    return this.tab;
};
// TODO: refactor hide/show
jpicDivTab.prototype.show = function() {
    $('div.'+this.id).show();
};
jpicDivTab.prototype.hide = function() {
    $('div.'+this.id).hide();
};
jpicTab = function(name, error) {
    this.name = name;
    this.error = error;
    this.id = 'id_' + URLify(this.name, 253);
    this.conditions = [];
};
jpicTab.prototype.getHtml = function() {
    var extra = '';
    if (this.error)
    {
        extra += 'style="color:red"';
    }

    return '<a href="#" '+extra+' class="jpic_tab '+this.id+'">'+this.name+'</a>';
};
jpicTab.prototype.assert = assert;
jpicTab.prototype.hide = function() {
    $('a.'+this.id).hide();
};
jpicTab.prototype.show = function() {
    $('a.'+this.id).show();
};

// sort of singleton
var jpicTabManager = new function() {
    this.fieldsets = [];
};
jpicTabManager.addTabContent = function(fieldset) {
    if (fieldset)
    {
        this.fieldsets[fieldset.id] = fieldset;
    }
};
jpicTabManager.parseDjangoAdmin = function() {
    var first = 0;
    
    $("fieldset.module").each(function() {
        var fieldset = jpicDjangoAdmin.factory($(this));
        jpicTabManager.addTabContent(fieldset);
    });

    $("div.inline-group").each(function() {
        var fieldset = jpicDjangoAdmin.factory($(this));
        fieldset.stacked = true; // will use stacked inline hide/show functions
        jpicTabManager.addTabContent(fieldset);
    });
};
jpicTabManager.parseDivTabs = function() {
    $("div.tab").each(function() {
        var divtab = jpicDivTab.factory($(this));
        jpicTabManager.addTabContent(divtab);
    });
};
jpicTabManager.writeTabs = function(element) {
    if (element === undefined)
    {
        if (String(document.location).toLowerCase().indexOf('popup') < 0)
        {
            $(".breadcrumbs").after().html($(".breadcrumbs").html() + '<div id="jpic_tab_list"></div>');
        }
        else
        {
            $("h1").html($('h1').html() + '<div id="jpic_tab_list"></div>');
        }
        element = $('#jpic_tab_list');
    }

    var links = [];
    for(var tabid in this.fieldsets)
    {
        var tab = this.fieldsets[tabid].getTab();
        links.push(tab.getHtml());
    }

    element.html('<ul><li>' + links.join('</li><li>') + '</li></ul>');
    
    for(var tabid in this.fieldsets)
    {
        tab = this.fieldsets[tabid].getTab();

        // connect the tab
        $('a.' + tab.id).click(function(e) {
            e.preventDefault();

            clslist = $(this).attr('class').split(' ');
            for (var i in clslist)
            {
                if (clslist[i].substr(0, 3) == 'id_')
                {
                    break;
                }
            }

            jpicTabManager.select(clslist[i]);
        });
    }
};
jpicTabManager.select = function(tabid) {
    for(var curtabid in this.fieldsets)
    {
        if (curtabid == tabid)
        {
            this.fieldsets[curtabid].show();
            $('a.'+tabid).addClass('selected');
        }
        else
        {
           this.fieldsets[curtabid].hide();
            $('a.'+tabid).removeClass('selected');
        }
    }
};
// }}}
// {{{ condition objects
var jpicFieldValueNotLike = function(field, value) {
    this.field = field;
    this.value = value;
    this.verb = 'like';
    this.verbose = this.field.name + ' ' + this.verb  + ' ' + this.value;
};
jpicFieldValueNotLike.prototype.assert = function() {
    var test = new RegExp(this.value, 'gi');

    if (test.test(this.field.getValue()))
    {
        return false;
    }
    else
    {
        return true;
    }
};
var jpicFieldValueLike = function(field, value) {
    this.field = field;
    this.value = value;
    this.verb = 'like';
    this.verbose = this.field.name + ' ' + this.verb  + ' ' + this.value;
};
jpicFieldValueLike.prototype.assert = function() {
    var test = new RegExp(this.value, 'gi');

    if (test.test(this.field.getValue()))
    {
        return true;
    }
    else
    {
        return false;
    }
};

var jpicFieldValueNotEqual = function(field, value) {
    this.field = field;
    this.value = value;
    this.verb = 'not equal';
    this.verbose = this.field.name + ' ' + this.verb  + ' ' + this.value;
};
jpicFieldValueNotEqual.prototype.assert = function() {
    this.verbose = this.field.name + ' ' + this.verb  + ' ' + this.value;
    this.verbose+= ' actually equal to "'+this.field.getValue()+'"';

    if (this.field.getValue() == this.value)
    {
        return false;
    }
    else
    {
        return true;
    }
};

// i should figure how to prototype the constructor when refactoring (later)
var jpicFieldValueEqual = function(field, value) {
    this.field = field;
    this.value = value;
    this.verb = 'equal';
};
jpicFieldValueEqual.prototype.assert = function() {
    this.verbose = this.field.name + ' (with value: "'+ this.field.getValue() +'") ' + this.verb  + ' "' + this.value +'"';

    if (this.field.value == this.value)
    {
        return true;
    }
    else
    {
        return false;
    }
};

var jpicFieldValueEqualOrUnset = function(field, value) {
    this.field = field;
    this.value = value;
    this.verb = 'unset or equal to';
    this.verbose = this.field.name + ' ' + this.verb  + ' ' + this.value;
};

jpicFieldValueEqualOrUnset.prototype.assert = function() {
    var value = this.field.getValue();
    if (!value)
    {
        return true;
    }

    if (value == this.value)
    {
        return true;
    }
    else
    {
        return false;
    }
};
// }}}
// {{{ ui
ui = new function() {
    this.items = [];
};
ui.writeTabs = function(element) {
    jpicTabManager.writeTabs(element);
}
ui.parseTabManager = function() {
    for(tabid in jpicTabManager.fieldsets)
    {
        fieldset = jpicTabManager.fieldsets[tabid];
        this.items[fieldset.name] = fieldset.getTab();
    }
}
/*
 * Moves field with sourceFieldName after destinationFieldName, on the same row.
 *
 * Tested with sourceFieldName alone in a row.
 */
ui.moveItemAfter = function(sourceFieldName, destinationFieldName) {
    var sourceItem = this.getOrCreateField(sourceFieldName);
    var destinationItem = this.getOrCreateField(destinationFieldName);

    destinationItem.row.addClass(sourceFieldName);
    sourceItem.row.removeClass(sourceFieldName);

    sourceItem.container.addClass('field-box');
    destinationItem.container.addClass('field-box');
    
    sourceItem.container.appendTo(destinationItem.row);
    sourceItem.row.removeClass('form-row');

    // todo: figure how to remove sourceItem.row before setting the new one
    sourceItem.row = destinationItem.row;
}
/*
 * Moves row that has field with name sourceFieldName in a new row at the end of tab of field destinationFieldName.
 *
 * Tested with sourceFieldName alone in a row.
 */
ui.appendToTab = function(sourceFieldName, destinationFieldName) {
    var sourceItem = this.getOrCreateField(sourceFieldName);
    var destinationItem = this.getOrCreateField(destinationFieldName);
    sourceItem.row.appendTo(destinationItem.row.parent());
}
ui.update = function() {
    for(name in this.items)
    {
        var item = this.items[name];
        var assert = item.assert();
        if (assert)
        {
            item.show();
        }
        else
        {
            item.hide();
        }
    }
};
ui.addItem = function(item) {
    this.items[item.name] = item;
};
ui.getItem = function(itemName) {
    if (this.items[itemName] === undefined)
    {
        console.error(this);
    }

    return this.items[itemName];
};
ui.addItem = function(item) {
    this.items[item.name] = item;
};
ui.getOrCreateField = function(fieldName) {
    if (this.items[fieldName] === undefined)
    {
        var field = new jpicField(fieldName);
        this.addItem(field);
    }
    return this.getItem(fieldName);
};
ui.addConstraint = function(slaves, master, masterValues, conditionFunction) {
    if(!is_array(slaves))
    {
        slaves = [slaves,];
    }
    if(!is_array(masterValues))
    {
        masterValues = [masterValues,];
    }

    for (var i=0; i<slaves.length; i++)
    {
        for (var j=0; j<masterValues.length; j++)
        {
            if (conditionFunction === undefined)
            {
                conditionFunction = jpicFieldValueEqualOrUnset;
            }
        
            var slave = this.getOrCreateField(slaves[i]);
            var masterField = this.getOrCreateField(master);
            var condition = new conditionFunction(masterField, masterValues[j]);
            slave.conditions.push(condition);
        }
    }
};
// }}}
/*members assert, conditions, field, getValue, hide, id, items, length, 
    name, prototype, show, update, val, value
*/

