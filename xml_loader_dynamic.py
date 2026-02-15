"""
Enhanced OneSumX/RiskPro XML Data Loader - SCHEMA-FLEXIBLE VERSION

This loader dynamically discovers and extracts ALL attributes from XML files
without requiring hard-coded field mappings. Future-proof for evolving schemas.

Key Features:
- Dynamic attribute discovery
- Schema-flexible parsing
- Comprehensive attribute extraction
- Stress scenario ready
- Full transparency and logging

Author: ALM Risk Engineering Team
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any, Set
from pathlib import Path
from collections import defaultdict
import logging
import pandas as pd

from alm_scenarios.models import (
    RiskFactor, Counterparty, Contract, ContractType,
    YieldCurve, SpreadCurve, FXRate, EquityIndex, MacroFactor
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def parse_onesumx_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse OneSumX date format: '1/10/2024 AM' or '5/12/2024 AM'"""
    if not date_str:
        return None
    
    try:
        date_clean = date_str.replace(' AM', '').replace(' PM', '').strip()
        return datetime.strptime(date_clean, '%m/%d/%Y')
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None


def parse_term_to_years(term_str: str) -> float:
    """Convert OneSumX term strings to years (1M → 0.0833, 5Y → 5.0)"""
    term_str = term_str.strip().upper()
    
    if term_str.endswith('M'):
        months = int(term_str[:-1])
        return months / 12.0
    elif term_str.endswith('Y'):
        years = int(term_str[:-1])
        return float(years)
    elif term_str.endswith('D'):
        days = int(term_str[:-1])
        return days / 365.0
    else:
        logger.warning(f"Unknown term format: {term_str}")
        return 0.0


def parse_boolean(value: str) -> Optional[bool]:
    """Parse boolean from string"""
    if not value:
        return None
    value_lower = value.strip().lower()
    if value_lower in ('true', 'yes', '1'):
        return True
    elif value_lower in ('false', 'no', '0'):
        return False
    return None


# =============================================================================
# DYNAMIC ATTRIBUTE EXTRACTION ENGINE
# =============================================================================

class AttributeExtractor:
    """
    Dynamically extracts all attributes from XML elements without schema knowledge.
    
    This class discovers and extracts:
    - Direct text values
    - Attributes (@name, @code, etc.)
    - Nested reference values
    - Free-defined attributes
    """
    
    def __init__(self):
        self.discovered_fields = defaultdict(lambda: {'count': 0, 'samples': set(), 'type': None})
    
    def extract_all_attributes(self, elem: ET.Element, prefix: str = '') -> Dict[str, Any]:
        """
        Recursively extract all attributes from an XML element.
        
        Returns a flat dictionary with all discovered attributes:
        - Simple fields: {'cpName': 'Apple Inc.', 'sovereign': False}
        - Reference fields: {'segment': 'Corporates', 'country_code': 'BE'}
        - Nested fields: {'risk_profile': 'Manufacturing'}
        
        Args:
            elem: XML element to extract from
            prefix: Field name prefix (for nested structures)
        
        Returns:
            Dictionary of all attributes
        """
        attributes = {}
        
        for child in elem:
            field_name = child.tag
            
            # Record for schema discovery
            full_path = f"{prefix}/{field_name}" if prefix else field_name
            self.discovered_fields[full_path]['count'] += 1
            
            # Extract text content
            if child.text and child.text.strip():
                value = child.text.strip()
                attributes[field_name] = value
                
                # Store sample for discovery
                if len(self.discovered_fields[full_path]['samples']) < 5:
                    self.discovered_fields[full_path]['samples'].add(value)
                
                # Infer type
                if not self.discovered_fields[full_path]['type']:
                    if value.lower() in ('true', 'false'):
                        self.discovered_fields[full_path]['type'] = 'boolean'
                    elif value.replace('.', '').replace('-', '').isdigit():
                        self.discovered_fields[full_path]['type'] = 'numeric'
                    else:
                        self.discovered_fields[full_path]['type'] = 'text'
            
            # Extract attributes (like @name, @code)
            if child.attrib:
                for attr_name, attr_value in child.attrib.items():
                    # Create meaningful field names
                    if attr_name == 'name':
                        # Use parent tag as field name
                        field_key = self._normalize_field_name(field_name)
                    elif attr_name == 'code':
                        field_key = f"{self._normalize_field_name(field_name)}_code"
                    else:
                        field_key = f"{self._normalize_field_name(field_name)}_{attr_name}"
                    
                    attributes[field_key] = attr_value
                    
                    # Record for discovery
                    attr_path = f"{full_path}@{attr_name}"
                    self.discovered_fields[attr_path]['count'] += 1
                    if len(self.discovered_fields[attr_path]['samples']) < 5:
                        self.discovered_fields[attr_path]['samples'].add(attr_value)
                    self.discovered_fields[attr_path]['type'] = 'reference'
            
            # Handle nested structures (recurse but flatten into parent)
            if len(list(child)) > 0:
                nested_attrs = self.extract_all_attributes(child, full_path)
                # Merge nested attributes with prefix to avoid collisions
                for nested_key, nested_value in nested_attrs.items():
                    # Use parent tag as prefix for clarity
                    prefixed_key = f"{self._normalize_field_name(field_name)}_{nested_key}"
                    if prefixed_key not in attributes:  # Avoid overwriting direct values
                        attributes[prefixed_key] = nested_value
        
        return attributes
    
    def _normalize_field_name(self, field_name: str) -> str:
        """
        Normalize OneSumX field names to Python-friendly format.
        
        Examples:
            cpName → cp_name
            CADCRCounterpartyClass → cad_cr_counterparty_class
            CurrencyDefinition → currency
        """
        # Remove common prefixes for clarity
        if field_name.startswith('cp'):
            field_name = field_name[2:]  # cpName → Name
        
        # Remove Definition/Class suffixes
        field_name = field_name.replace('Definition', '').replace('Class', '')
        
        # Convert camelCase to snake_case
        import re
        field_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', field_name)
        field_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', field_name)
        
        return field_name.lower().strip('_')
    
    def get_discovered_schema(self) -> Dict[str, Any]:
        """
        Get the discovered schema from all processed elements.
        
        Returns:
            Dictionary with field statistics and samples
        """
        schema = {}
        for field_path, info in sorted(self.discovered_fields.items()):
            schema[field_path] = {
                'count': info['count'],
                'type': info['type'],
                'samples': list(info['samples'])[:3]
            }
        return schema
    
    def print_discovered_schema(self, entity_type: str = "Entity"):
        """Print discovered schema in a readable format"""
        logger.info(f"\n{'='*70}")
        logger.info(f"DISCOVERED {entity_type.upper()} ATTRIBUTES")
        logger.info(f"{'='*70}")
        logger.info(f"Total unique fields: {len(self.discovered_fields)}\n")
        
        for field_path in sorted(self.discovered_fields.keys()):
            info = self.discovered_fields[field_path]
            logger.info(f"✓ {field_path}")
            logger.info(f"  Count: {info['count']} | Type: {info['type'] or 'unknown'}")
            if info['samples']:
                samples_str = ', '.join(str(s)[:30] for s in list(info['samples'])[:3])
                logger.info(f"  Samples: {samples_str}")
        
        logger.info(f"\n{'='*70}\n")


# =============================================================================
# ENHANCED COUNTERPARTY LOADING
# =============================================================================

def load_counterparties_from_xml_dynamic(
    counterparties_xml_path: str,
    creditrisk_xml_path: Optional[str] = None,
    return_dataframe: bool = True
) -> Tuple[List[Counterparty], Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Load counterparties with DYNAMIC attribute extraction.
    
    This function:
    1. Discovers all attributes present in the XML
    2. Extracts them without hard-coded mappings
    3. Returns both Counterparty objects and detailed DataFrame
    4. Provides schema discovery report
    
    Args:
        counterparties_xml_path: Path to counterparties XML
        creditrisk_xml_path: Optional path to credit risk relations XML
        return_dataframe: If True, also return DataFrame with all attributes
    
    Returns:
        Tuple of:
        - List of Counterparty objects (for compatibility)
        - DataFrame with all attributes (if return_dataframe=True)
        - Dictionary with discovered schema
    """
    logger.info(f"Loading counterparties with dynamic attribute extraction...")
    logger.info(f"Source: {Path(counterparties_xml_path).name}")
    
    tree = ET.parse(counterparties_xml_path)
    root = tree.getroot()
    model = root.find('Model')
    cp_editor = model.find('counterpartyEditor')
    
    if cp_editor is None:
        logger.warning("  ⚠ No counterpartyEditor section found")
        return [], None, {}
    
    # Initialize attribute extractor
    extractor = AttributeExtractor()
    
    # Storage for all counterparty data
    counterparties_data = []
    counterparties_objects = []
    
    # Process each counterparty
    for cp_elem in cp_editor.findall('Counterparty'):
        # Extract ALL attributes dynamically
        attributes = extractor.extract_all_attributes(cp_elem)
        
        # Get primary identifier
        counterparty_id = attributes.get('sourceSystemRecordNumber', attributes.get('name', f'CP_{len(counterparties_data)}'))
        
        # Create Counterparty object for compatibility with existing system
        # Note: Only pass parameters that Counterparty class accepts
        # All attributes are preserved in DataFrame for analysis
        counterparty_obj = Counterparty(
            counterparty_id=counterparty_id,
            name=attributes.get('cpName', counterparty_id),
            country=attributes.get('legal_country_country_code', attributes.get('country_code')),
            # segment removed - not accepted by Counterparty class
            pd=None,  # Will be populated from credit risk
            recovery_rate=None,
            rating=None
        )
        
        counterparties_objects.append(counterparty_obj)
        
        # Store full attributes for DataFrame
        attributes['_counterparty_id'] = counterparty_id  # Add ID for indexing
        counterparties_data.append(attributes)
    
    # Print discovered schema
    extractor.print_discovered_schema("Counterparty")
    
    logger.info(f"✓ Loaded {len(counterparties_objects)} counterparties with full attribute extraction")
    
    # Create DataFrame if requested
    df = None
    if return_dataframe and counterparties_data:
        df = pd.DataFrame(counterparties_data)
        logger.info(f"✓ Created DataFrame with {len(df.columns)} attributes:")
        for col in sorted(df.columns):
            non_null = df[col].notna().sum()
            logger.info(f"  - {col}: {non_null}/{len(df)} populated")
    
    # Load credit risk data if provided
    if creditrisk_xml_path:
        logger.info(f"\nLoading credit risk data from {Path(creditrisk_xml_path).name}...")
        
        try:
            tree2 = ET.parse(creditrisk_xml_path)
            root2 = tree2.getroot()
            model2 = root2.find('Model')
            rating_obs_section = model2.find('counterpartyRatingObservation')
            
            if rating_obs_section is not None:
                # Build lookup by counterparty ID
                cp_by_id = {cp.counterparty_id: cp for cp in counterparties_objects}
                rating_count = 0
                
                for rating_obs in rating_obs_section.findall('CounterpartyRatingObservation'):
                    # Extract rating data dynamically
                    rating_attrs = extractor.extract_all_attributes(rating_obs)
                    
                    # Try to find counterparty reference
                    cp_id = None
                    for key, value in rating_attrs.items():
                        if 'counterparty' in key.lower() and 'recordnumber' in key.lower():
                            cp_id = value
                            break
                    
                    # Get rating
                    rating_class = rating_attrs.get('ratingClass', rating_attrs.get('rating_class'))
                    
                    if cp_id and cp_id in cp_by_id and rating_class:
                        rating_class = rating_class.strip()
                        if rating_class:
                            cp_by_id[cp_id].rating = rating_class
                            rating_count += 1
                            
                            # Also update DataFrame if exists
                            if df is not None:
                                df.loc[df['_counterparty_id'] == cp_id, 'rating'] = rating_class
                
                logger.info(f"✓ Added ratings to {rating_count} counterparties")
        
        except Exception as e:
            logger.warning(f"  ⚠ Error loading credit risk data: {e}")
    
    # Get discovered schema
    discovered_schema = extractor.get_discovered_schema()
    
    return counterparties_objects, df, discovered_schema


# =============================================================================
# ENHANCED RISK FACTOR LOADING (keeping existing implementation)
# =============================================================================

def load_risk_factors_from_model_xml(model_xml_path: str) -> List[RiskFactor]:
    """Load risk factor DEFINITIONS from model XML (existing implementation)"""
    logger.info(f"Loading risk factor definitions from {Path(model_xml_path).name}...")
    
    tree = ET.parse(model_xml_path)
    root = tree.getroot()
    model = root.find('Model')
    
    risk_factors = []
    
    # Load yield curves
    yc_section = model.find('yieldCurve')
    if yc_section is not None:
        for yc in yc_section.findall('YieldCurveDefinition'):
            factor_id = yc.find('matrixCode')
            factor_id = factor_id.text if factor_id is not None and factor_id.text else None
            if not factor_id:
                name_elem = yc.find('n')
                factor_id = name_elem.text if name_elem is not None and name_elem.text else None
            
            if not factor_id:
                continue
            
            name_elem = yc.find('n')
            name = name_elem.text if name_elem is not None and name_elem.text else factor_id
            
            currency_elem = yc.find('.//CurrencyDefinition')
            currency = currency_elem.get('name') if currency_elem is not None else None
            
            desc_elem = yc.find('description')
            description = desc_elem.text if desc_elem is not None and desc_elem.text else None
            
            risk_factors.append(YieldCurve(
                factor_id=factor_id,
                currency=currency,
                description=description or name,
                tenors=[],  # Empty for now - can be populated if needed
                rates=[]    # Empty for now
            ))
    
    # Load stock indices
    si_section = model.find('stockIndex')
    if si_section is not None:
        for si in si_section.findall('StockIndexDefinition'):
            matrix_elem = si.find('matrixCode')
            name_elem = si.find('n')
            factor_id = (matrix_elem.text if matrix_elem is not None and matrix_elem.text 
                        else name_elem.text if name_elem is not None and name_elem.text else None)
            if not factor_id:
                continue
            
            name = name_elem.text if name_elem is not None and name_elem.text else factor_id
            currency_elem = si.find('currency/CurrencyDefinition')
            currency = currency_elem.get('name') if currency_elem is not None else None
            desc_elem = si.find('description')
            description = desc_elem.text if desc_elem is not None and desc_elem.text else None
            
            risk_factors.append(EquityIndex(
                factor_id=factor_id,
                currency=currency,
                description=description or name,
                index_name=name,
                current_level=0.0  # Will be populated from observations if available
            ))
    
    # Load spread curves
    spread_section = model.find('spreadCurveDefinition')
    if spread_section is not None:
        for sc in spread_section.findall('SpreadCurveDefinition'):
            matrix_elem = sc.find('matrixCode')
            name_elem = sc.find('n')
            factor_id = (matrix_elem.text if matrix_elem is not None and matrix_elem.text 
                        else name_elem.text if name_elem is not None and name_elem.text else None)
            if not factor_id:
                continue
            
            name = name_elem.text if name_elem is not None and name_elem.text else factor_id
            desc_elem = sc.find('description')
            description = desc_elem.text if desc_elem is not None and desc_elem.text else None
            
            risk_factors.append(SpreadCurve(
                factor_id=factor_id,
                description=description or name,
                tenors=[],  # Empty for now
                spreads=[]  # Empty for now
            ))
    
    # Load consumer price indices
    cpi_section = model.find('consumerPriceIndex')
    if cpi_section is not None:
        for cpi in cpi_section.findall('ConsumerPriceIndexDefinition'):
            matrix_elem = cpi.find('matrixCode')
            name_elem = cpi.find('n')
            factor_id = (matrix_elem.text if matrix_elem.text is not None and matrix_elem.text 
                        else name_elem.text if name_elem is not None and name_elem.text else None)
            if not factor_id:
                continue
            
            name = name_elem.text if name_elem is not None and name_elem.text else factor_id
            currency_elem = cpi.find('currency/CurrencyDefinition')
            currency = currency_elem.get('name') if currency_elem is not None else None
            desc_elem = cpi.find('description')
            description = desc_elem.text if desc_elem is not None and desc_elem.text else None
            
            risk_factors.append(MacroFactor(
                factor_id=factor_id,
                currency=currency,
                description=description or name,
                macro_type="CPI",
                current_value=0.0,  # Will be populated from observations
                unit="%"
            ))
    
    logger.info(f"  ✓ Loaded {len(risk_factors)} risk factor definitions")
    return risk_factors


# =============================================================================
# ENHANCED OBSERVATIONS LOADING (keeping existing implementation)
# =============================================================================

def load_observations_from_xml(
    observations_xml_paths: List[str],
    risk_factors: List[RiskFactor],
    latest_only: bool = True
) -> List[RiskFactor]:
    """Load market data observations and attach to risk factors (existing implementation)"""
    logger.info(f"Loading market observations from {len(observations_xml_paths)} file(s)...")
    
    rf_by_name = {}
    for rf in risk_factors:
        rf_by_name[rf.factor_id] = rf
        if rf.description and '.' in rf.description:
            rf_by_name[rf.description] = rf
    
    observations_count = 0
    populated_factors = set()
    
    for obs_path in observations_xml_paths:
        logger.info(f"  Processing {Path(obs_path).name}...")
        
        try:
            tree = ET.parse(obs_path)
            root = tree.getroot()
            model = root.find('Model')
            
            # Process yield curve observations
            yc_obs_section = model.find('yieldCurveObs')
            if yc_obs_section is not None:
                curve_observations = {}
                
                for yc_obs in yc_obs_section.findall('YieldCurveObservation'):
                    curve_def = yc_obs.find('yieldCurveDefinition/YieldCurveDefinition')
                    curve_name = curve_def.get('name') if curve_def is not None else None
                    obs_date_elem = yc_obs.find('observationDate')
                    obs_date_str = obs_date_elem.text if obs_date_elem is not None else None
                    obs_date = parse_onesumx_date(obs_date_str)
                    
                    if not curve_name or not obs_date:
                        continue
                    
                    yield_points = yc_obs.find('yieldPoints')
                    if yield_points is None:
                        continue
                    
                    points = []
                    for yp in yield_points.findall('YieldPoint'):
                        term_elem = yp.find('term')
                        rate_elem = yp.find('rate')
                        
                        if term_elem is not None and term_elem.text and rate_elem is not None and rate_elem.text:
                            term_years = parse_term_to_years(term_elem.text)
                            rate_value = float(rate_elem.text)
                            points.append((term_years, rate_value))
                    
                    if points:
                        if curve_name not in curve_observations:
                            curve_observations[curve_name] = []
                        curve_observations[curve_name].append((obs_date, points))
                
                # Attach to risk factors
                for curve_name, obs_list in curve_observations.items():
                    if curve_name in rf_by_name:
                        obs_list.sort(key=lambda x: x[0], reverse=True)
                        latest_date, latest_points = obs_list[0]
                        
                        latest_points.sort(key=lambda x: x[0])
                        terms, rates = zip(*latest_points) if latest_points else ([], [])
                        
                        rf = rf_by_name[curve_name]
                        # YieldCurve uses tenors and rates
                        if hasattr(rf, 'tenors'):
                            rf.tenors = [f"{t}Y" for t in terms]  # Convert to tenor format
                            rf.rates = list(rates)
                        
                        populated_factors.add(curve_name)
                        observations_count += 1
            
            # Process FX observations
            fx_obs_section = model.find('fxObs')
            if fx_obs_section is not None:
                fx_observations = {}
                
                for fx_obs in fx_obs_section.findall('FxRateObservation'):
                    currency_elem = fx_obs.find('currencyFrom/CurrencyDefinition')
                    currency_from = currency_elem.get('name') if currency_elem is not None else None
                    price_elem = fx_obs.find('price')
                    price_str = price_elem.text if price_elem is not None else None
                    obs_date_elem = fx_obs.find('observationDate')
                    obs_date_str = obs_date_elem.text if obs_date_elem is not None else None
                    obs_date = parse_onesumx_date(obs_date_str)
                    
                    if currency_from and price_str and obs_date:
                        factor_id = f"FX_{currency_from}"
                        
                        if factor_id not in fx_observations:
                            fx_observations[factor_id] = []
                        
                        fx_observations[factor_id].append((obs_date, float(price_str)))
                
                for factor_id, obs_list in fx_observations.items():
                    if factor_id not in rf_by_name:
                        currency_from = factor_id.replace('FX_', '')
                        base_curr = currency_from[:3] if len(currency_from) >= 6 else currency_from
                        quote_curr = currency_from[3:] if len(currency_from) >= 6 else "CHF"
                        rf = FXRate(
                            factor_id=factor_id,
                            currency_pair=currency_from,
                            base_currency=base_curr,
                            quote_currency=quote_curr,
                            spot_rate=0.0,  # Will be set below
                            description=f"FX rate {currency_from}"
                        )
                        risk_factors.append(rf)
                        rf_by_name[factor_id] = rf
                    
                    obs_list.sort(key=lambda x: x[0], reverse=True)
                    latest_date, latest_rate = obs_list[0]
                    
                    rf = rf_by_name[factor_id]
                    rf.spot_rate = latest_rate
                    
                    populated_factors.add(factor_id)
                    observations_count += 1
            
            # Process macro economic factor observations
            macro_obs_section = model.find('macroEconomicFactorObs')
            if macro_obs_section is not None:
                macro_observations = {}
                
                for macro_obs in macro_obs_section.findall('MacroEconomicFactorObservation'):
                    factor_elem = macro_obs.find('macroEconomicFactor/MacroEconomicFactor')
                    factor_name = factor_elem.get('name') if factor_elem is not None else None
                    value_elem = macro_obs.find('value')
                    value_str = value_elem.text if value_elem is not None else None
                    obs_date_elem = macro_obs.find('observationDate')
                    obs_date_str = obs_date_elem.text if obs_date_elem is not None else None
                    obs_date = parse_onesumx_date(obs_date_str)
                    
                    if factor_name and value_str and obs_date:
                        if factor_name not in macro_observations:
                            macro_observations[factor_name] = []
                        
                        macro_observations[factor_name].append((obs_date, float(value_str)))
                
                for factor_name, obs_list in macro_observations.items():
                    factor_id = f"MACRO_{factor_name}"
                    
                    if factor_id not in rf_by_name:
                        rf = MacroFactor(
                            factor_id=factor_id,
                            macro_type=factor_name,
                            current_value=0.0,  # Will be set below
                            description=f"Macro factor {factor_name}"
                        )
                        risk_factors.append(rf)
                        rf_by_name[factor_id] = rf
                    
                    obs_list.sort(key=lambda x: x[0], reverse=True)
                    latest_date, latest_value = obs_list[0]
                    
                    rf = rf_by_name[factor_id]
                    rf.current_value = latest_value
                    
                    populated_factors.add(factor_id)
                    observations_count += 1
        
        except Exception as e:
            logger.warning(f"  ⚠ Error processing {Path(obs_path).name}: {e}")
            continue
    
    logger.info(f"  ✓ Loaded {observations_count} observations for {len(populated_factors)} risk factors")
    
    unpopulated = [rf.factor_id for rf in risk_factors if rf.factor_id not in populated_factors and rf.factor_type == 'yield_curve']
    if unpopulated:
        logger.warning(f"  ⚠ {len(unpopulated)} yield curves without observations: {unpopulated[:5]}...")
    
    return risk_factors


# =============================================================================
# ENHANCED CONTRACT LOADING WITH DYNAMIC ATTRIBUTE EXTRACTION
# =============================================================================

def map_contract_type(discriminator: str):
    """
    Map OneSumX discriminator to contract type string.
    Returns string to avoid enum dependency issues.
    """
    mapping = {
        'RGM': 'LOAN',
        'PAM': 'BOND',
        'IRSWP': 'SWAP',
        'STK': 'EQUITY',
        'ANN': 'LOAN',
        'UMP': 'DEPOSIT',
        'VAL': 'OTHER'
    }
    return mapping.get(discriminator, 'OTHER')


def string_to_contract_type(type_string: str):
    """
    Safely convert string to ContractType enum.
    Falls back to available enum values if exact match not found.
    """
    # Try to get the enum value, with fallbacks
    type_mapping = {
        'LOAN': 'LOAN',
        'BOND': 'BOND',
        'SWAP': 'SWAP',
        'DEPOSIT': 'DEPOSIT',
        'EQUITY': 'LOAN',  # Fallback if EQUITY doesn't exist
        'OTHER': 'LOAN'    # Fallback if OTHER doesn't exist
    }
    
    safe_type = type_mapping.get(type_string, 'LOAN')
    
    # Try to get the enum attribute, fallback to LOAN if it doesn't exist
    try:
        return getattr(ContractType, safe_type)
    except AttributeError:
        # If even LOAN doesn't exist, just return the string
        return safe_type


def load_contracts_from_xml_dynamic(
    contracts_xml_path: str,
    limit: Optional[int] = None,
    return_dataframe: bool = True
) -> Tuple[List[Contract], Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Load contracts with DYNAMIC attribute extraction.
    
    This function:
    1. Discovers all attributes present in the XML
    2. Extracts them without hard-coded mappings
    3. Returns both Contract objects and detailed DataFrame
    4. Provides schema discovery report
    
    Args:
        contracts_xml_path: Path to contracts XML
        limit: Optional limit on number of contracts to load
        return_dataframe: If True, also return DataFrame with all attributes
    
    Returns:
        Tuple of:
        - List of Contract objects (for compatibility)
        - DataFrame with all attributes (if return_dataframe=True)
        - Dictionary with discovered schema
    """
    logger.info(f"Loading contracts with dynamic attribute extraction...")
    logger.info(f"Source: {Path(contracts_xml_path).name}")
    if limit:
        logger.info(f"  Limiting to {limit} contracts")
    
    tree = ET.parse(contracts_xml_path)
    root = tree.getroot()
    model = root.find('Model')
    contract_editor = model.find('contractEditor')
    
    if contract_editor is None:
        logger.warning("  ⚠ No contractEditor section found")
        return [], None, {}
    
    # Initialize attribute extractor
    extractor = AttributeExtractor()
    
    # Storage for all contract data
    contracts_data = []
    contracts_objects = []
    contract_types_count = {}
    
    # Process each contract
    contract_list = list(contract_editor)[:limit] if limit else list(contract_editor)
    
    for contract_elem in contract_list:
        # Extract ALL attributes dynamically
        attributes = extractor.extract_all_attributes(contract_elem)
        
        # Get primary identifiers
        contract_id = attributes.get('sourceSystemRecordNumber', f'CONTRACT_{len(contracts_data)}')
        discriminator = attributes.get('discriminator', 'UNKNOWN')
        contract_type = map_contract_type(discriminator)
        contract_types_count[contract_type] = contract_types_count.get(contract_type, 0) + 1
        
        # Extract key financial fields for Contract object (with fallbacks)
        currency = attributes.get('currency_currency', attributes.get('currency'))
        
        # Try to find notional/principal
        notional = None
        for key in ['currentPrincipal', 'notionalPrincipal', 'principal']:
            if key in attributes:
                try:
                    notional = abs(float(attributes[key]))
                    break
                except (ValueError, TypeError):
                    continue
        
        # Try to find interest rate
        interest_rate = None
        for key in ['currentNominalInterestRate', 'nominalInterestRate', 'interestRate', 'rate']:
            if key in attributes:
                try:
                    interest_rate = float(attributes[key])
                    break
                except (ValueError, TypeError):
                    continue
        
        # Parse maturity date
        maturity_date = None
        for key in ['maturityDate', 'endDate', 'terminationDate']:
            if key in attributes:
                maturity_date = parse_onesumx_date(attributes[key])
                if maturity_date:
                    break
        
        # Extract pricing/discount curves
        pricing_curve = None
        discount_curve = None
        for key, value in attributes.items():
            if 'pricing' in key.lower() and 'curve' in key.lower():
                pricing_curve = value
            if 'discount' in key.lower() and 'curve' in key.lower():
                discount_curve = value
        
        # Convert string contract_type to enum for Contract object
        contract_type_enum = string_to_contract_type(contract_type)
        
        # Create Contract object for compatibility
        # Note: Contract class has very limited parameters, so we only pass what it accepts
        # All rich data is preserved in the DataFrame for analysis
        try:
            contract_obj = Contract(
                contract_id=contract_id,
                contract_type=contract_type_enum,
                currency=currency,
                notional=notional,
                maturity_date=maturity_date,
                counterparty_id=None
            )
        except TypeError as e:
            # If even these fail, create with minimal parameters
            logger.warning(f"  ⚠ Could not create full Contract object: {e}")
            contract_obj = Contract(
                contract_id=contract_id,
                contract_type=contract_type_enum
            )
        
        # Store all the rich data as attributes on the object for access
        contract_obj.discriminator = discriminator
        contract_obj.interest_rate = interest_rate
        contract_obj.pricing_curve = pricing_curve
        contract_obj.discount_curve = discount_curve
        contract_obj.all_attributes = attributes  # Store ALL discovered attributes
        
        contracts_objects.append(contract_obj)
        
        # Store full attributes for DataFrame
        attributes['_contract_id'] = contract_id
        attributes['_contract_type'] = contract_type  # Already a string from map_contract_type
        attributes['_discriminator'] = discriminator
        contracts_data.append(attributes)
    
    # Print discovered schema
    extractor.print_discovered_schema("Contract")
    
    logger.info(f"✓ Loaded {len(contracts_objects)} contracts with full attribute extraction")
    
    # Show contract type distribution
    logger.info(f"  Contract types:")
    for ctype, count in sorted(contract_types_count.items(), key=lambda x: -x[1]):
        logger.info(f"    - {ctype}: {count}")  # ctype is already a string from map_contract_type
    
    # Create DataFrame if requested
    df = None
    if return_dataframe and contracts_data:
        df = pd.DataFrame(contracts_data)
        logger.info(f"✓ Created DataFrame with {len(df.columns)} attributes:")
        
        # Show key financial attributes
        key_attrs = ['_contract_id', '_contract_type', '_discriminator', 'currency_currency', 
                    'currentPrincipal', 'notionalPrincipal', 'currentNominalInterestRate',
                    'maturityDate', 'dealDate']
        
        for col in df.columns:
            if any(key in col for key in key_attrs):
                non_null = df[col].notna().sum()
                logger.info(f"  - {col}: {non_null}/{len(df)} populated")
    
    # Get discovered schema
    discovered_schema = extractor.get_discovered_schema()
    
    return contracts_objects, df, discovered_schema


# =============================================================================
# DYNAMIC OBSERVATIONS/RISK FACTORS LOADING
# =============================================================================

def load_observations_from_xml_dynamic(
    observations_xml_paths: List[str],
    return_dataframe: bool = True
) -> Tuple[List, Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Load market observations/risk factors with DYNAMIC attribute extraction.
    
    This function:
    1. Discovers all observation types present in the XML
    2. Extracts them without hard-coded type mappings  
    3. Returns both simple list and detailed DataFrame
    4. Provides schema discovery report
    
    Args:
        observations_xml_paths: List of paths to observation XML files
        return_dataframe: If True, also return DataFrame with all attributes
    
    Returns:
        Tuple of:
        - List of observation dictionaries (for compatibility)
        - DataFrame with all attributes (if return_dataframe=True)
        - Dictionary with discovered schema
    """
    logger.info(f"Loading observations with dynamic attribute extraction...")
    logger.info(f"Processing {len(observations_xml_paths)} file(s)")
    
    # Initialize attribute extractor
    extractor = AttributeExtractor()
    
    # Storage for all observation data
    observations_data = []
    observations_by_type = defaultdict(int)
    files_processed = 0
    
    for obs_path in observations_xml_paths:
        logger.info(f"  Processing {Path(obs_path).name}...")
        
        try:
            tree = ET.parse(obs_path)
            root = tree.getroot()
            model = root.find('Model')
            
            if model is None:
                logger.warning(f"    ⚠ No Model section found")
                continue
            
            # Dynamically find ALL observation sections
            # Don't hard-code section names - discover them!
            for section in model:
                section_tag = section.tag
                
                # Skip non-observation sections
                if 'Obs' not in section_tag and 'observation' not in section_tag.lower():
                    continue
                
                obs_count = len(list(section))
                if obs_count == 0:
                    continue
                
                logger.info(f"    Found {section_tag}: {obs_count} observations")
                
                # Process each observation in this section
                for obs_elem in section:
                    # Extract ALL attributes dynamically
                    attributes = extractor.extract_all_attributes(obs_elem)
                    
                    # Add metadata about source
                    attributes['_observation_type'] = section_tag
                    attributes['_observation_element'] = obs_elem.tag
                    attributes['_source_file'] = Path(obs_path).name
                    
                    # Try to extract key identifiers
                    obs_id = None
                    
                    # Look for factor/currency identifiers
                    for key, value in attributes.items():
                        if any(x in key.lower() for x in ['factor', 'currency', 'index', 'curve']):
                            if 'name' in key.lower() or key.endswith('_name'):
                                obs_id = value
                                break
                    
                    if not obs_id:
                        obs_id = f"{section_tag}_{len(observations_data)}"
                    
                    attributes['_factor_id'] = obs_id
                    
                    observations_data.append(attributes)
                    observations_by_type[section_tag] += 1
            
            files_processed += 1
            
        except Exception as e:
            logger.warning(f"    ⚠ Error processing {Path(obs_path).name}: {e}")
            continue
    
    # Print discovered schema
    extractor.print_discovered_schema("Observation/Risk Factor")
    
    logger.info(f"✓ Loaded {len(observations_data)} observations from {files_processed} file(s)")
    
    # Show observation type distribution
    logger.info(f"  Observation types:")
    for obs_type, count in sorted(observations_by_type.items(), key=lambda x: -x[1]):
        logger.info(f"    - {obs_type}: {count}")
    
    # Create DataFrame if requested
    df = None
    if return_dataframe and observations_data:
        df = pd.DataFrame(observations_data)
        logger.info(f"✓ Created DataFrame with {len(df.columns)} attributes")
        
        # Show key attributes
        key_attrs = ['_factor_id', '_observation_type', 'observationDate', 'value', 'price', 'rate']
        for col in df.columns:
            if any(key in col for key in key_attrs):
                non_null = df[col].notna().sum()
                logger.info(f"  - {col}: {non_null}/{len(df)} populated")
    
    # Get discovered schema
    discovered_schema = extractor.get_discovered_schema()
    
    # Create simple list for compatibility
    observations_list = observations_data.copy()
    
    return observations_list, df, discovered_schema


# =============================================================================
# UNIFIED LOADER WITH DYNAMIC EXTRACTION
# =============================================================================

def load_model_parameters_from_xml_dynamic(
    model_xml: str,
    return_dataframe: bool = True
) -> Tuple[Dict[str, Any], Optional[pd.DataFrame], Optional[Dict]]:
    """
    Dynamically load model parameters from XML with full attribute extraction.
    
    This function extracts ALL model configuration parameters without requiring
    hard-coded field mappings. Future-proof for evolving schemas.
    
    Args:
        model_xml: Path to model XML file
        return_dataframe: If True, returns DataFrame with all discovered attributes
    
    Returns:
        Tuple of (model_params_dict, dataframe, schema_metadata)
        - model_params_dict: Nested dictionary with all model parameters
        - dataframe: DataFrame with flattened parameters (optional)
        - schema_metadata: Discovery metadata including attribute coverage
    """
    logger.info("="*80)
    logger.info("LOADING MODEL PARAMETERS - DYNAMIC ATTRIBUTE EXTRACTION")
    logger.info("="*80)
    logger.info(f"Model XML: {model_xml}")
    
    try:
        tree = ET.parse(model_xml)
        root = tree.getroot()
        model = root.find('Model')
        
        if model is None:
            logger.warning("No <Model> element found in XML")
            return {}, None, None
        
        # Initialize extractor
        extractor = AttributeExtractor()
        
        # Extract all parameters dynamically
        model_params = {}
        parameter_records = []
        
        # Track all sections found
        sections_found = []
        
        for section in model:
            section_name = section.tag
            sections_found.append(section_name)
            
            logger.info(f"Processing section: <{section_name}>")
            
            # Extract all attributes from this section
            section_data = extractor.extract_all_attributes(section, prefix=section_name)
            
            if section_data:
                model_params[section_name] = section_data
                
                # For tabular representation, create a record
                record = {
                    'section': section_name,
                    'section_element_count': len(section),
                }
                record.update(section_data)
                parameter_records.append(record)
        
        logger.info(f"\n✓ Found {len(sections_found)} model configuration sections:")
        for sec in sections_found:
            logger.info(f"  - {sec}")
        
        # Create DataFrame if requested
        params_df = None
        schema_metadata = None
        
        if return_dataframe and parameter_records:
            params_df = pd.DataFrame(parameter_records)
            
            # Generate schema metadata (similar to other loaders)
            schema_metadata = {
                'total_sections': len(sections_found),
                'section_names': sections_found,
                'total_attributes': len(params_df.columns) if params_df is not None else 0,
                'attributes': []
            }
            
            if params_df is not None:
                # Analyze attribute coverage
                total_records = len(params_df)
                for col in params_df.columns:
                    populated = params_df[col].notna().sum()
                    coverage = (populated / total_records * 100) if total_records > 0 else 0
                    
                    # Get sample values
                    samples = params_df[col].dropna().astype(str).unique()[:5].tolist()
                    
                    schema_metadata['attributes'].append({
                        'name': col,
                        'total': total_records,
                        'populated': int(populated),
                        'coverage': round(coverage, 1),
                        'samples': samples
                    })
                
                logger.info(f"\n✓ Discovered {len(params_df.columns)} parameter attributes")
                logger.info(f"✓ Total configuration entries: {len(params_df)}")
        
        logger.info("="*80)
        logger.info("")
        
        return model_params, params_df, schema_metadata
        
    except Exception as e:
        logger.error(f"Error loading model parameters: {e}")
        import traceback
        traceback.print_exc()
        return {}, None, None


def load_from_xml(
    model_xml: Optional[str] = None,
    contracts_xml: Optional[str] = None,
    counterparties_xml: Optional[str] = None,
    creditrisk_xml: Optional[str] = None,
    observations_xmls: Optional[List[str]] = None,
    limit_contracts: Optional[int] = None,
    load_risk_factors: bool = True,
    load_counterparties: bool = True,
    load_contracts: bool = True,
    return_enriched: bool = True
) -> Tuple[List[RiskFactor], List[Counterparty], List[Contract], Optional[Dict[str, Any]]]:
    """
    Enhanced XML loader with DYNAMIC ATTRIBUTE EXTRACTION.
    
    Returns:
        Tuple of (risk_factors, counterparties, contracts, enriched_data)
        
        enriched_data contains:
        - 'counterparties_df': DataFrame with all counterparty attributes
        - 'discovered_schema': Dictionary with discovered attribute schema
    """
    logger.info("="*80)
    logger.info("LOADING ALM DATA FROM XML FILES - DYNAMIC ATTRIBUTE EXTRACTION")
    logger.info("="*80)
    
    risk_factors = []
    counterparties = []
    contracts = []
    enriched_data = {}
    
    # Load risk factors from model XML
    if load_risk_factors and model_xml:
        risk_factors = load_risk_factors_from_model_xml(model_xml)
        
        # ALSO load model parameters dynamically (NEW!)
        if return_enriched:
            model_params, model_params_df, model_params_schema = load_model_parameters_from_xml_dynamic(
                model_xml,
                return_dataframe=True
            )
            enriched_data['model_params'] = model_params
            enriched_data['model_params_df'] = model_params_df
            enriched_data['model_params_schema'] = model_params_schema
    
    # Load observations - INDEPENDENT of model XML!
    if observations_xmls:
        # Use old loader to populate/extend risk_factors for compatibility
        risk_factors = load_observations_from_xml(observations_xmls, risk_factors)
        
        # Also use dynamic loader to get enriched DataFrame
        if return_enriched:
            obs_list, obs_df, obs_schema = load_observations_from_xml_dynamic(
                observations_xmls,
                return_dataframe=True
            )
            enriched_data['observations_df'] = obs_df
            enriched_data['observations_schema'] = obs_schema
    
    # Load counterparties with DYNAMIC extraction
    if load_counterparties and counterparties_xml:
        counterparties, cp_df, discovered_schema = load_counterparties_from_xml_dynamic(
            counterparties_xml, 
            creditrisk_xml,
            return_dataframe=return_enriched
        )
        
        if return_enriched:
            enriched_data['counterparties_df'] = cp_df
            enriched_data['discovered_schema'] = discovered_schema
    
    # Load contracts with dynamic extraction
    if load_contracts and contracts_xml:
        contracts, contracts_df, contracts_schema = load_contracts_from_xml_dynamic(
            contracts_xml, 
            limit_contracts,
            return_dataframe=return_enriched
        )
        
        if return_enriched:
            enriched_data['contracts_df'] = contracts_df
            enriched_data['contracts_schema'] = contracts_schema
    
    logger.info("")
    logger.info("="*80)
    logger.info("XML LOADING COMPLETE - WITH DYNAMIC ATTRIBUTE EXTRACTION")
    logger.info("="*80)
    logger.info(f"✓ Risk factors: {len(risk_factors)}")
    logger.info(f"✓ Counterparties: {len(counterparties)}")
    logger.info(f"✓ Contracts: {len(contracts)}")
    if enriched_data.get('model_params_df') is not None:
        logger.info(f"✓ Model parameters: {len(enriched_data['model_params_df'])} sections")
        logger.info(f"✓ Model parameter attributes: {len(enriched_data['model_params_df'].columns)}")
    if enriched_data.get('counterparties_df') is not None:
        logger.info(f"✓ Counterparty attributes: {len(enriched_data['counterparties_df'].columns)}")
    if enriched_data.get('contracts_df') is not None:
        logger.info(f"✓ Contract attributes: {len(enriched_data['contracts_df'].columns)}")
    if enriched_data.get('observations_df') is not None:
        logger.info(f"✓ Observations: {len(enriched_data['observations_df'])} records")
        logger.info(f"✓ Observation attributes: {len(enriched_data['observations_df'].columns)}")
    logger.info("")
    
    return risk_factors, counterparties, contracts, enriched_data


if __name__ == "__main__":
    # Test dynamic XML loading
    import sys
    from pathlib import Path
    
    test_dir = Path(".")
    if (Path("/mnt/user-data/uploads")).exists():
        test_dir = Path("/mnt/user-data/uploads")
    
    counterparties_xml = test_dir / "ALM_Model_XML_1-counterparties.xml"
    creditrisk_xml = test_dir / "ALM_Model_XML_1-creditriskrelations.xml"
    
    if counterparties_xml.exists():
        print("\n" + "="*80)
        print("TESTING DYNAMIC COUNTERPARTY EXTRACTION")
        print("="*80)
        
        cp_list, cp_df, schema = load_counterparties_from_xml_dynamic(
            str(counterparties_xml),
            str(creditrisk_xml) if creditrisk_xml.exists() else None,
            return_dataframe=True
        )
        
        print("\n" + "="*80)
        print("SAMPLE COUNTERPARTY DATA")
        print("="*80)
        if cp_df is not None and len(cp_df) > 0:
            print("\nFirst counterparty (all attributes):")
            print(cp_df.iloc[0].to_dict())
            
            print("\nDataFrame shape:", cp_df.shape)
            print("\nAll columns:", list(cp_df.columns))
    else:
        print("No XML files found for testing")
